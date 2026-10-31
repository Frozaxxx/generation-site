"""
Сборка сайта (этап Б) - граф LangGraph.

    START ─┬─ copy ──────┬─ render ─ check ─ package
           ├─ translate ─┘    ▲
           └─ reuse ──────────┘   (тексты прошлой версии той же ревизии и языка - бесплатно)

Факты берутся из снимка утверждённой карточки и в модель не отдаются на «переписывание»:
модель пишет только подачу (заголовки, подводки, meta) и переводит тексты карточки.
"""

from typing import Any, TypedDict

import asyncio
import logging
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from src.core.settings import storage_config
from src.jobs.application.runner import JobContext, SessionFactory
from src.llm.application.protocols import LLMClient

from ..domain.entities import SiteVersion
from ..domain.enums import SiteLanguage
from ..domain.themes import get_theme
from ..infra.database.repos.sites import SqlSiteVersionRepository
from .checks import check_site
from .drafts import SiteCopyDraft, TranslationDraft
from .prompts import copy_prompt, translation_prompt
from .render import SiteRenderer, zip_site
from .texts import all_texts, facts_numbers, translatable_texts

logger = logging.getLogger(__name__)

STAGES = ["texts", "render", "check", "package"]
STAGE_LABELS = {
    "texts": "Тексты сайта и перевод",
    "render": "Сборка страниц",
    "check": "Проверка сайта",
    "package": "Архив и сохранение",
}


def site_dir(site_id: UUID) -> Any:
    return storage_config.sites_dir / str(site_id)


def site_archive(site_id: UUID) -> Any:
    return storage_config.sites_dir / f"{site_id}.zip"


class SiteState(TypedDict, total=False):
    site_id: UUID
    company_id: UUID
    company_revision: int
    snapshot: dict[str, Any]
    language: SiteLanguage
    theme: str
    accent: str | None
    model: str
    reuse: dict[str, Any] | None
    reused_from: UUID | None
    copy: dict[str, Any]
    texts: dict[str, str]
    pages: list[str]
    issues: list[dict[str, str]]


def _context(config: RunnableConfig) -> JobContext:
    return config["configurable"]["job"]  # pyright: ignore[reportTypedDictNotRequiredAccess]


class SiteBuilder:
    def __init__(self, llm: LLMClient, session_factory: SessionFactory) -> None:
        self._llm = llm
        self._session_factory = session_factory
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        graph = StateGraph(SiteState)
        graph.add_node("copy", self._copy)
        graph.add_node("translate", self._translate)
        graph.add_node("reuse", self._reuse)
        graph.add_node("render", self._render)
        graph.add_node("check", self._check)
        graph.add_node("package", self._package)

        graph.add_conditional_edges(START, self._route, ["copy", "translate", "reuse"])
        graph.add_edge(["copy", "translate"], "render")
        graph.add_edge("reuse", "render")
        graph.add_edge("render", "check")
        graph.add_edge("check", "package")
        graph.add_edge("package", END)
        return graph.compile()

    async def __call__(self, context: JobContext) -> UUID:
        params = context.params
        state: SiteState = await self._graph.ainvoke(
            {
                "site_id": UUID(params["site_id"]),
                "company_id": UUID(params["company_id"]),
                "company_revision": params["company_revision"],
                "snapshot": params["snapshot"],
                "language": SiteLanguage(params["language"]),
                "theme": params["theme"],
                "accent": params.get("accent"),
                "model": params["model"],
                "reuse": params.get("reuse"),
            },
            config={"configurable": {"job": context}},
        )
        return state["site_id"]

    @staticmethod
    def _route(state: SiteState) -> list[str]:
        return ["reuse"] if state.get("reuse") else ["copy", "translate"]

    async def _reuse(self, state: SiteState, config: RunnableConfig) -> dict:
        context = _context(config)
        await context.stage("texts", "Тексты прошлой версии с той же ревизией и языком")
        reuse = state["reuse"] or {}
        return {
            "copy": reuse["copy"],
            "texts": reuse["texts"],
            "reused_from": UUID(reuse["site_id"]),
        }

    async def _copy(self, state: SiteState, config: RunnableConfig) -> dict:
        context = _context(config)
        await context.stage("texts", STAGE_LABELS["texts"])

        snapshot = state["snapshot"]
        system, user = copy_prompt(snapshot, state["language"])
        draft = await self._llm.complete_json(
            model=state["model"],
            system=system,
            user=user,
            schema=SiteCopyDraft.with_facts(facts_numbers(snapshot), snapshot["brand"]["name"]),
            budget=context.budget,
            temperature=0.7,
            max_tokens=3000,
        )
        return {"copy": draft.model_dump()}

    async def _translate(self, state: SiteState, config: RunnableConfig) -> dict:
        snapshot = state["snapshot"]
        if state["language"] is SiteLanguage.RU:
            # Карточка на русском: тексты идут на сайт без изменений.
            return {"texts": all_texts(snapshot)}

        context = _context(config)
        await context.stage("texts", STAGE_LABELS["texts"])

        brand = snapshot["brand"]["name"]

        async def one(group: str, texts: dict[str, str]) -> dict[str, str]:
            if not texts:
                return {}
            system, user = translation_prompt(texts, brand)
            draft = await self._llm.complete_json(
                model=state["model"],
                system=system,
                user=user,
                schema=TranslationDraft.for_texts(texts),
                budget=context.budget,
                temperature=0.3,
                max_tokens=10000,
            )
            await context.note(f"Переведено: {group}")
            return draft.items

        groups = translatable_texts(snapshot)
        results = await asyncio.gather(*(one(group, texts) for group, texts in groups.items()))
        merged: dict[str, str] = {}
        for result in results:
            merged.update(result)
        return {"texts": merged}

    async def _render(self, state: SiteState, config: RunnableConfig) -> dict:
        context = _context(config)
        await context.stage("render", STAGE_LABELS["render"])

        renderer = SiteRenderer(site_dir(state["site_id"]))
        result = await asyncio.to_thread(
            renderer.render,
            company_id=state["company_id"],
            snapshot=state["snapshot"],
            texts=state["texts"],
            copy_text=state["copy"],
            language=state["language"],
            theme=get_theme(state["theme"], state.get("accent")),
        )
        return {"pages": result.pages}

    async def _check(self, state: SiteState, config: RunnableConfig) -> dict:
        context = _context(config)
        await context.stage("check", STAGE_LABELS["check"])
        issues = await asyncio.to_thread(
            check_site,
            site_dir(state["site_id"]),
            snapshot=state["snapshot"],
            language=state["language"],
        )
        return {"issues": issues}

    async def _package(self, state: SiteState, config: RunnableConfig) -> dict:
        context = _context(config)
        await context.stage("package", STAGE_LABELS["package"])

        site_id = state["site_id"]
        domain = state["snapshot"]["brand"]["domain"].split(".")[0]

        async with self._session_factory() as session:
            repo = SqlSiteVersionRepository(session)
            number = await repo.next_number(state["company_id"])
            root = f"{domain}-v{number}-{state['language'].value}"
            await asyncio.to_thread(zip_site, site_dir(site_id), site_archive(site_id), root)

            site = SiteVersion.create(
                site_id=site_id,
                company_id=state["company_id"],
                company_revision=state["company_revision"],
                number=number,
                language=state["language"],
                theme=state["theme"],
                accent=state.get("accent"),
                snapshot=state["snapshot"],
                content={"copy": state["copy"], "texts": state["texts"]},
                issues=state.get("issues", []),
                pages=state.get("pages", []),
                cost_usd=context.budget.spent_usd,
                requests=context.budget.requests,
                reused_from=state.get("reused_from"),
            )
            await repo.create(site)
            await session.commit()
        return {}
