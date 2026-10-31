import random
import secrets
from dataclasses import replace
from uuid import UUID

from src.core.settings import openrouter_config
from src.jobs.application.runner import JobRunner
from src.jobs.domain.entities import Job
from src.jobs.domain.enums import JobKind
from src.llm.application.protocols import LLMClient
from src.llm.domain.budget import OperationBudget
from src.shared.application.transaction import Transaction
from src.shared.domain.exceptions import NotFoundError

from ...domain.catalog.people import NAME_ORIGINS, OFFICES
from ...domain.entities import Company
from ...domain.profile import Photo
from ...domain.serialization import profile_to_dict
from ..repos import CompanyRepository
from .drafts import ReviewDraft
from .facts import GenerationRequest, PersonSkeleton, random_appearance
from .photos import save_team_photo
from .pipeline import STAGES, CompanyGenerator
from .prompts import photo_prompt, review_prompt


class CompanyGenerationService:
    """Запуск генерации компании в фоне."""

    def __init__(self, runner: JobRunner, generator: CompanyGenerator) -> None:
        self._runner = runner
        self._generator = generator

    async def start(self, request: GenerationRequest, budget: OperationBudget) -> Job:
        stages = STAGES if request.with_photos else [s for s in STAGES if s != "photos"]
        params = {
            "request": {
                "brand_name": request.brand_name,
                "country": request.country,
                "direction": request.direction,
                "service_type": request.service_type,
                "scale": request.scale.value if request.scale else None,
                "model": request.model,
                "with_photos": request.with_photos,
                "custom_direction": request.custom_direction,
                "custom_service": request.custom_service,
            },
            # Зерно делает выбор фактов воспроизводимым для отладки.
            "seed": secrets.randbits(63),
        }
        return await self._runner.submit(
            kind=JobKind.COMPANY,
            stages=stages,
            params=params,
            handler=self._generator,
            budget=budget,
        )


class CompanyAIService:
    """Платные действия над существующей компанией: смысловая проверка и новое фото."""

    def __init__(
        self,
        company_repo: CompanyRepository,
        transaction: Transaction,
        llm: LLMClient,
    ) -> None:
        self._company_repo = company_repo
        self._transaction = transaction
        self._llm = llm

    async def _get(self, company_id: UUID) -> Company:
        company = await self._company_repo.read(company_id)
        if company is None:
            raise NotFoundError(f"Компания {company_id} не найдена")
        return company

    async def review(self, company_id: UUID, model: str, budget: OperationBudget) -> Company:
        company = await self._get(company_id)
        system, user = review_prompt(profile_to_dict(company.profile))
        result = await self._llm.complete_json(
            model=model,
            system=system,
            user=user,
            schema=ReviewDraft,
            budget=budget,
            temperature=0.2,
            max_tokens=2000,
        )
        company.record_review([issue.model_dump() for issue in result.issues])
        self._add_cost(company, budget)

        await self._company_repo.upsert(company)
        await self._transaction()
        return company

    async def regenerate_photo(
        self,
        company_id: UUID,
        person_id: str,
        budget: OperationBudget,
    ) -> Company:
        company = await self._get(company_id)
        person = company.profile.person(person_id)
        if person is None:
            raise NotFoundError(f"Сотрудник {person_id} не найден")

        rng = random.Random()  # noqa: S311 - не криптография
        heritage = next(
            (o.heritage for o in NAME_ORIGINS if person.last_name in o.last_names),
            "Central European",
        )
        setting = (company.generation.concept.get("фон фото") if company.generation else None) or (
            OFFICES[0]
        )
        skeleton = PersonSkeleton(
            id=person.id,
            first_name=person.first_name,
            last_name=person.last_name,
            gender=person.gender,
            age=person.age,
            role=person.role,
            department=person.department,
            heritage=heritage,
            appearance=random_appearance(rng, person.gender),
        )

        image = await self._llm.generate_image(
            model=openrouter_config.image_model,
            prompt=photo_prompt(skeleton, setting),
            budget=budget,
        )
        relpath = save_team_photo(company.id, person.id, image.content)
        company.set_photo(
            person.id, Photo(file=relpath, alt=f"{person.full_name}, {person.position}")
        )
        self._add_cost(company, budget)

        await self._company_repo.upsert(company)
        await self._transaction()
        return company

    @staticmethod
    def _add_cost(company: Company, budget: OperationBudget) -> None:
        if company.generation is None:
            return
        info = company.generation
        company.generation = replace(
            info,
            cost_usd=round(info.cost_usd + budget.spent_usd, 6),
            input_tokens=info.input_tokens + budget.input_tokens,
            output_tokens=info.output_tokens + budget.output_tokens,
            requests=info.requests + budget.requests,
        )
