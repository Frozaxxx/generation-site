"""
Генерация компании (этап А).

concept → product → team → review → photos → save. Каждый шаг отмечается в задаче,
расходы считаются общим бюджетом операции.
"""

import logging
import random
import time
from dataclasses import replace
from uuid import UUID, uuid4

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
from .drafts import ConceptDraft, PersonDraft, ProductDraft, ReviewDraft, TeamDraft
from .facts import CompanyFacts, GenerationRequest, build_facts, resolve_params
from .photos import save_team_photo
from .prompts import concept_prompt, photo_prompt, product_prompt, review_prompt, team_prompt

logger = logging.getLogger(__name__)

STAGES = ["concept", "product", "team", "review", "photos", "save"]
STAGE_LABELS = {
    "concept": "Концепция, история и аудитория",
    "product": "Продукт и FAQ",
    "team": "Команда и биографии",
    "review": "Проверка на противоречия",
    "photos": "Фотографии команды",
    "save": "Сохранение карточки",
}
AVOID_LIMIT = 12


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


class CompanyGenerator:
    def __init__(self, llm: LLMClient, session_factory: SessionFactory) -> None:
        self._llm = llm
        self._session_factory = session_factory

    async def __call__(self, context: JobContext) -> UUID:
        started = time.monotonic()
        request = GenerationRequest(**context.params["request"])
        rng = random.Random(context.params["seed"])  # noqa: S311 - не криптография

        params = resolve_params(request, rng)
        facts = build_facts(params, rng)
        model = params.model
        budget = context.budget

        await context.stage("concept", STAGE_LABELS["concept"])
        system, user = concept_prompt(facts, await self._recent_concepts())
        concept = await self._llm.complete_json(
            model=model,
            system=system,
            user=user,
            schema=ConceptDraft.bounded(facts.founded_year, facts.current_year),
            budget=budget,
            temperature=1.0,
            max_tokens=4000,
        )
        if params.brand_name:
            concept = concept.model_copy(update={"brand_name": params.brand_name})

        await context.stage("product", STAGE_LABELS["product"])
        concept_data = concept.model_dump()
        system, user = product_prompt(facts, concept_data)
        product = await self._llm.complete_json(
            model=model,
            system=system,
            user=user,
            schema=ProductDraft,
            budget=budget,
            temperature=0.8,
            max_tokens=5000,
        )

        await context.stage("team", STAGE_LABELS["team"])
        system, user = team_prompt(facts, concept_data, product.model_dump())
        team = await self._llm.complete_json(
            model=model,
            system=system,
            user=user,
            schema=TeamDraft.for_people([person.id for person in facts.team]),
            budget=budget,
            temperature=0.9,
            max_tokens=4000,
        )

        profile = assemble_profile(facts, concept, product, team)

        await context.stage("review", STAGE_LABELS["review"])
        warnings: list[str] = []
        review = await self._review(profile, model, context, warnings)

        company_id = uuid4()
        if request.with_photos:
            await context.stage("photos", STAGE_LABELS["photos"])
            profile = await self._photos(company_id, profile, facts, context, warnings)

        await context.stage("save", STAGE_LABELS["save"])
        company = Company.create(
            company_id=company_id,
            params=params,
            profile=profile,
            generation=self._info(model, context, started, facts, concept, review, warnings),
        )

        async with self._session_factory() as session:
            await SqlCompanyRepository(session).create(company)
            await session.commit()

        return company.id

    async def _recent_concepts(self) -> list[dict[str, str]]:
        async with self._session_factory() as session:
            return await SqlCompanyRepository(session).recent_concepts(AVOID_LIMIT)

    async def _review(
        self,
        profile: CompanyProfile,
        model: str,
        context: JobContext,
        warnings: list[str],
    ) -> list[dict[str, str]]:
        """Смысловая проверка. Её сбой не должен ронять уже оплаченную генерацию."""

        system, user = review_prompt(profile_to_dict(profile))
        try:
            result = await self._llm.complete_json(
                model=model,
                system=system,
                user=user,
                schema=ReviewDraft,
                budget=context.budget,
                temperature=0.2,
                max_tokens=2000,
            )
        except (LLMError, BudgetExceededError) as error:
            warnings.append(f"Смысловая проверка не выполнена: {error.message}")
            return []
        return [issue.model_dump() for issue in result.issues]

    async def _photos(
        self,
        company_id: UUID,
        profile: CompanyProfile,
        facts: CompanyFacts,
        context: JobContext,
        warnings: list[str],
    ) -> CompanyProfile:
        skeletons = {person.id: person for person in facts.team}
        team = []
        for index, person in enumerate(profile.team, start=1):
            await context.note(f"Фото {index} из {len(profile.team)}: {person.full_name}")
            try:
                image = await self._llm.generate_image(
                    model=openrouter_config.image_model,
                    prompt=photo_prompt(skeletons[person.id], facts.photo_setting),
                    budget=context.budget,
                )
                relpath = save_team_photo(company_id, person.id, image.content)
            except (LLMError, BudgetExceededError, OSError, ValueError) as error:
                message = getattr(error, "message", type(error).__name__)
                warnings.append(f"Фото {person.full_name} не создано: {message}")
                logger.warning("Team photo failed", extra={"person_id": person.id})
                team.append(person)
                continue

            team.append(
                replace(
                    person,
                    photo=Photo(file=relpath, alt=f"{person.full_name}, {person.position}"),
                )
            )
        return replace(profile, team=team)

    @staticmethod
    def _info(
        model: str,
        context: JobContext,
        started: float,
        facts: CompanyFacts,
        concept: ConceptDraft,
        review: list[dict[str, str]],
        warnings: list[str],
    ) -> GenerationInfo:
        budget = context.budget
        return GenerationInfo(
            model=model,
            cost_usd=round(budget.spent_usd, 6),
            input_tokens=budget.input_tokens,
            output_tokens=budget.output_tokens,
            requests=budget.requests,
            duration_seconds=round(time.monotonic() - started, 1),
            concept={**facts.seeds, "ниша": concept.niche, "фон фото": facts.photo_setting},
            review=review,
            review_revision=1,
            warnings=warnings,
        )
