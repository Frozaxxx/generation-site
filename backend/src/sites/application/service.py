import shutil
from uuid import UUID, uuid4

from src.companies.application.repos import CompanyRepository
from src.companies.domain.serialization import profile_to_dict
from src.jobs.application.runner import JobRunner
from src.jobs.domain.entities import Job
from src.jobs.domain.enums import JobKind
from src.llm.domain.budget import OperationBudget
from src.shared.domain.exceptions import InvalidStateError, NotFoundError

from ..domain.entities import SiteVersion
from ..domain.enums import SiteLanguage
from ..domain.themes import get_theme
from ..infra.database.repos.sites import SqlSiteVersionRepository
from .pipeline import STAGES, SiteBuilder, site_archive, site_dir


class SiteService:
    def __init__(
        self,
        company_repo: CompanyRepository,
        site_repo: SqlSiteVersionRepository,
        runner: JobRunner,
        builder: SiteBuilder,
    ) -> None:
        self._companies = company_repo
        self._sites = site_repo
        self._runner = runner
        self._builder = builder

    async def start(
        self,
        company_id: UUID,
        *,
        language: SiteLanguage,
        theme: str,
        accent: str | None,
        reuse_texts: bool,
        model: str,
        budget: OperationBudget,
    ) -> Job:
        """Запускает сборку новой версии сайта из утверждённой карточки."""

        get_theme(theme, accent)  # проверка темы и цвета до запуска
        company = await self._companies.read(company_id)
        if company is None:
            raise NotFoundError(f"Компания {company_id} не найдена")
        if not company.is_approved:
            raise InvalidStateError("Сайт собирается только из утверждённой карточки")

        without_photo = [person.full_name for person in company.profile.team if not person.photo]
        if without_photo:
            raise InvalidStateError(
                "У каждого человека на сайте должно быть фото",
                details={"without_photo": without_photo},
            )

        reuse = None
        if reuse_texts:
            previous = await self._sites.reusable(company.id, company.revision, language)
            if previous is not None:
                reuse = {
                    "site_id": str(previous.id),
                    "copy": previous.content["copy"],
                    "texts": previous.content["texts"],
                }

        stages = STAGES
        params = {
            "site_id": str(uuid4()),
            "company_id": str(company.id),
            "company_revision": company.revision,
            # Снимок фактов на момент запуска: правки карточки во время сборки не попадут.
            "snapshot": profile_to_dict(company.profile),
            "language": language.value,
            "theme": theme,
            "accent": accent,
            "model": model,
            "reuse": reuse,
        }
        return await self._runner.submit(
            kind=JobKind.SITE,
            stages=stages,
            params=params,
            handler=self._builder,
            budget=budget,
            subject_id=company.id,
        )

    async def get(self, site_id: UUID) -> SiteVersion:
        site = await self._sites.read(site_id)
        if site is None:
            raise NotFoundError(f"Версия сайта {site_id} не найдена")
        return site

    async def by_company(self, company_id: UUID) -> list[SiteVersion]:
        return await self._sites.by_company(company_id)

    async def delete(self, site_id: UUID) -> None:
        await self.get(site_id)
        await self._sites.delete(site_id)
        remove_site_files(site_id)


def remove_site_files(site_id: UUID) -> None:
    shutil.rmtree(site_dir(site_id), ignore_errors=True)
    site_archive(site_id).unlink(missing_ok=True)
