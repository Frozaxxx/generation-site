"""
Генерация компании (этап А) - граф LangGraph.

    concept ─┬─ product ─┬─ assemble ─ review ─┬─ photos ─ save
             └─ team ────┘        ▲            │
                                  └── revise ◄─┘  (один круг, если проверка нашла
                                                   ошибки в продукте или слогане)

Продукт и команда пишутся параллельно: оба шага зависят только от концепции.
Фото генерируются по несколько одновременно. Этапы и расходы пишутся в задачу.
"""

from typing import Annotated, Any, TypedDict

import asyncio
import logging
import operator
import random
import time
from dataclasses import replace
from uuid import UUID, uuid4

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from src.core.settings import openrouter_config
from src.jobs.application.runner import JobContext, SessionFactory
from src.llm.application.protocols import LLMClient
from src.llm.domain.exceptions import BudgetExceededError, LLMError

from ...domain.entities import Company
from ...domain.enums import TeamRole
from ...domain.profile import (
    Audience,
    AudienceSegment,
    Benefit,
    CompanyProfile,
    FaqItem,
    History,
    Milestone,
    Person,
    Photo,
    ProcessStep,
    Product,
)
from ...domain.serialization import profile_to_dict
from ...domain.vo import GenerationInfo
from ...infra.database.repos.companies import SqlCompanyRepository
from .drafts import (
    ConceptDraft,
    PersonDraft,
    ProductDraft,
    ReviewDraft,
    RevisionDraft,
    TeamDraft,
)
from .facts import CompanyFacts, GenerationRequest, build_facts, resolve_params
from .photos import save_team_photo
from .prompts import (
    concept_prompt,
    photo_prompt,
    product_prompt,
    review_prompt,
    revision_prompt,
    team_prompt,
)

logger = logging.getLogger(__name__)

STAGES = ["concept", "texts", "review", "photos", "save"]
STAGE_LABELS = {
    "concept": "Концепция, история и аудитория",
    "texts": "Продукт, FAQ и команда",
    "review": "Проверка на противоречия",
    "photos": "Фотографии команды",
    "save": "Сохранение карточки",
}
AVOID_LIMIT = 12
MAX_REVISIONS = 1
PHOTO_CONCURRENCY = 3
# Разделы, которые умеет исправлять шаг revise.
REVISABLE_PREFIXES = ("product", "faq", "brand.tagline")


class GenerationState(TypedDict, total=False):
    facts: CompanyFacts
    with_photos: bool
    avoid: list[dict[str, str]]
    concept: ConceptDraft
    product: ProductDraft
    team: TeamDraft
    profile: CompanyProfile
    review: list[dict[str, str]]
    revisions: int
    company_id: UUID
    # Параллельные ветки дописывают предупреждения, а не перезаписывают.
    warnings: Annotated[list[str], operator.add]


def assemble_profile(
    facts: CompanyFacts,
    concept: ConceptDraft,
    product: ProductDraft,
    team: TeamDraft,
) -> CompanyProfile:
    brand = facts.brand(concept.brand_name, concept.tagline)
    drafts: dict[str, PersonDraft] = {person.id: person for person in team.people}

    people = []
    for skeleton in facts.team:
        draft = drafts[skeleton.id]
        department = (
            None if skeleton.role is TeamRole.CEO else draft.department or skeleton.department
        )
        people.append(
            Person(
                id=skeleton.id,
                first_name=skeleton.first_name,
                last_name=skeleton.last_name,
                gender=skeleton.gender,
                age=skeleton.age,
                role=skeleton.role,
                position=draft.position,
                department=department,
                bio=draft.bio,
                experience=draft.experience,
                education=draft.education,
            )
        )

    return CompanyProfile(
        brand=brand,
        contacts=facts.contacts(brand.domain),
        history=History(
            founded_year=facts.founded_year,
            employees=facts.employees,
            founding_story=concept.founding_story,
            specialization=concept.specialization,
            milestones=[
                Milestone(year=item.year, title=item.title, description=item.description)
                for item in concept.milestones
            ],
        ),
        audience=Audience(
            segments=[
                AudienceSegment(name=item.name, description=item.description)
                for item in concept.segments
            ],
            client_problem=concept.client_problem,
        ),
        product=Product(
            name=concept.product_name,
            summary=product.summary,
            inputs=product.inputs,
            process=[
                ProcessStep(title=step.title, description=step.description)
                for step in product.process
            ],
            outputs=product.outputs,
            limitations=product.limitations,
            benefits=[
                Benefit(title=item.title, description=item.description)
                for item in product.benefits
            ],
            delivery=product.delivery,
        ),
        team=people,
        faq=[FaqItem(question=item.question, answer=item.answer) for item in product.faq],
    )


def _context(config: RunnableConfig) -> JobContext:
    return config["configurable"]["job"]  # pyright: ignore[reportTypedDictNotRequiredAccess]


def _model(state: GenerationState) -> str:
    return state["facts"].params.model


class CompanyGenerator:
    def __init__(self, llm: LLMClient, session_factory: SessionFactory) -> None:
        self._llm = llm
        self._session_factory = session_factory
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        graph = StateGraph(GenerationState)
        graph.add_node("concept", self._concept)
        graph.add_node("product", self._product)
        graph.add_node("team", self._team)
        graph.add_node("assemble", self._assemble)
        graph.add_node("review", self._review)
        graph.add_node("revise", self._revise)
        graph.add_node("photos", self._photos)
        graph.add_node("save", self._save)

        graph.add_edge(START, "concept")
        graph.add_edge("concept", "product")
        graph.add_edge("concept", "team")
        graph.add_edge(["product", "team"], "assemble")
        graph.add_edge("assemble", "review")
        graph.add_conditional_edges("review", self._after_review, ["revise", "photos", "save"])
        graph.add_edge("revise", "assemble")
        graph.add_edge("photos", "save")
        graph.add_edge("save", END)
        return graph.compile()

    async def __call__(self, context: JobContext) -> UUID:
        started = time.monotonic()
        request = GenerationRequest(**context.params["request"])
        rng = random.Random(context.params["seed"])  # noqa: S311 - не криптография

        params = resolve_params(request, rng)
        facts = build_facts(params, rng)

        async with self._session_factory() as session:
            avoid = await SqlCompanyRepository(session).recent_concepts(AVOID_LIMIT)

        state: GenerationState = await self._graph.ainvoke(
            {
                "facts": facts,
                "with_photos": request.with_photos,
                "avoid": avoid,
                "revisions": 0,
                "company_id": uuid4(),
                "warnings": [],
            },
            config={"configurable": {"job": context, "started": started}},
        )
        return state["company_id"]

    # ------------------------------------------------------------------
    # Узлы графа
    # ------------------------------------------------------------------

    async def _concept(self, state: GenerationState, config: RunnableConfig) -> dict:
        context = _context(config)
        facts = state["facts"]
        await context.stage("concept", STAGE_LABELS["concept"])

        system, user = concept_prompt(facts, state["avoid"])
        concept = await self._llm.complete_json(
            model=_model(state),
            system=system,
            user=user,
            schema=ConceptDraft.bounded(facts.founded_year, facts.current_year),
            budget=context.budget,
            temperature=1.0,
            max_tokens=4000,
        )
        if facts.params.brand_name:
            concept = concept.model_copy(update={"brand_name": facts.params.brand_name})
        return {"concept": concept}

    async def _product(self, state: GenerationState, config: RunnableConfig) -> dict:
        context = _context(config)
        await context.stage("texts", STAGE_LABELS["texts"])

        system, user = product_prompt(state["facts"], state["concept"].model_dump())
        product = await self._llm.complete_json(
            model=_model(state),
            system=system,
            user=user,
            schema=ProductDraft,
            budget=context.budget,
            temperature=0.8,
            max_tokens=5000,
        )
        return {"product": product}

    async def _team(self, state: GenerationState, config: RunnableConfig) -> dict:
        context = _context(config)
        await context.stage("texts", STAGE_LABELS["texts"])

        facts = state["facts"]
        system, user = team_prompt(facts, state["concept"].model_dump())
        team = await self._llm.complete_json(
            model=_model(state),
            system=system,
            user=user,
            schema=TeamDraft.for_people([person.id for person in facts.team]),
            budget=context.budget,
            temperature=0.9,
            max_tokens=4000,
        )
        return {"team": team}

    async def _assemble(self, state: GenerationState) -> dict:
        profile = assemble_profile(
            state["facts"], state["concept"], state["product"], state["team"]
        )
        return {"profile": profile}

    async def _review(self, state: GenerationState, config: RunnableConfig) -> dict:
        """Смысловая проверка. Её сбой не должен ронять уже оплаченную генерацию."""

        context = _context(config)
        await context.stage("review", STAGE_LABELS["review"])

        system, user = review_prompt(profile_to_dict(state["profile"]))
        try:
            result = await self._llm.complete_json(
                model=_model(state),
                system=system,
                user=user,
                schema=ReviewDraft,
                budget=context.budget,
                temperature=0.2,
                max_tokens=2000,
            )
        except (LLMError, BudgetExceededError) as error:
            return {
                "review": [],
                "warnings": [f"Смысловая проверка не выполнена: {error.message}"],
            }
        return {"review": [issue.model_dump() for issue in result.issues]}

    @staticmethod
    def _revisable(state: GenerationState) -> list[dict[str, str]]:
        return [
            issue
            for issue in state.get("review", [])
            if issue["severity"] == "error" and issue["path"].startswith(REVISABLE_PREFIXES)
        ]

    def _after_review(self, state: GenerationState) -> str:
        if self._revisable(state) and state["revisions"] < MAX_REVISIONS:
            return "revise"
        return "photos" if state["with_photos"] else "save"

    async def _revise(self, state: GenerationState, config: RunnableConfig) -> dict:
        context = _context(config)
        issues = self._revisable(state)
        await context.note(f"Исправляю замечания проверки: {len(issues)}")

        concept = state["concept"]
        system, user = revision_prompt(
            state["facts"], concept.model_dump(), state["product"].model_dump(), issues
        )
        try:
            revision = await self._llm.complete_json(
                model=_model(state),
                system=system,
                user=user,
                schema=RevisionDraft,
                budget=context.budget,
                temperature=0.4,
                max_tokens=5000,
            )
        except (LLMError, BudgetExceededError) as error:
            # Оставляем исходный текст: замечания всё равно увидит человек.
            return {
                "revisions": state["revisions"] + 1,
                "warnings": [f"Исправление по замечаниям не выполнено: {error.message}"],
            }

        return {
            "revisions": state["revisions"] + 1,
            "concept": concept.model_copy(update={"tagline": revision.tagline}),
            "product": ProductDraft.model_validate(revision.model_dump(exclude={"tagline"})),
        }

    async def _photos(self, state: GenerationState, config: RunnableConfig) -> dict:
        context = _context(config)
        await context.stage("photos", STAGE_LABELS["photos"])

        facts, profile, company_id = state["facts"], state["profile"], state["company_id"]
        skeletons = {person.id: person for person in facts.team}
        semaphore = asyncio.Semaphore(PHOTO_CONCURRENCY)
        done = 0

        async def one(person: Person) -> tuple[Person, str | None]:
            nonlocal done
            async with semaphore:
                try:
                    image = await self._llm.generate_image(
                        model=openrouter_config.image_model,
                        prompt=photo_prompt(skeletons[person.id], facts.photo_setting),
                        budget=context.budget,
                    )
                    relpath = save_team_photo(company_id, person.id, image.content)
                except (LLMError, BudgetExceededError, OSError, ValueError) as error:
                    logger.warning("Team photo failed", extra={"person_id": person.id})
                    message = getattr(error, "message", type(error).__name__)
                    return person, f"Фото {person.full_name} не создано: {message}"

                done += 1
                await context.note(f"Фото {done} из {len(profile.team)}")
                photo = Photo(file=relpath, alt=f"{person.full_name}, {person.position}")
                return replace(person, photo=photo), None

        results = await asyncio.gather(*(one(person) for person in profile.team))
        return {
            "profile": replace(profile, team=[person for person, _ in results]),
            "warnings": [warning for _, warning in results if warning],
        }

    async def _save(self, state: GenerationState, config: RunnableConfig) -> dict:
        context = _context(config)
        await context.stage("save", STAGE_LABELS["save"])

        facts, budget = state["facts"], context.budget
        started = config["configurable"]["started"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        info = GenerationInfo(
            model=facts.params.model,
            cost_usd=round(budget.spent_usd, 6),
            input_tokens=budget.input_tokens,
            output_tokens=budget.output_tokens,
            requests=budget.requests,
            duration_seconds=round(time.monotonic() - started, 1),
            concept={
                **facts.seeds,
                "ниша": state["concept"].niche,
                "фон фото": facts.photo_setting,
                "исправлений по проверке": str(state["revisions"]),
            },
            review=state.get("review", []),
            review_revision=1,
            warnings=state.get("warnings", []),
        )
        company = Company.create(
            company_id=state["company_id"],
            params=facts.params,
            profile=state["profile"],
            generation=info,
        )

        async with self._session_factory() as session:
            await SqlCompanyRepository(session).create(company)
            await session.commit()

        return {}
