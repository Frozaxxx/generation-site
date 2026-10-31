import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import FileResponse, RedirectResponse

from src.companies.dependencies import CompanyServiceDep
from src.jobs.application.dtos import JobRead
from src.llm.dependencies import ensure_llm_configured, new_budget, resolve_text_model
from src.shared.domain.exceptions import NotFoundError

from ...application.dtos import BuildSiteRequest, SiteRead, ThemeRead
from ...application.pipeline import site_archive, site_dir
from ...dependencies import SiteServiceDep
from ...domain.themes import THEMES

router = APIRouter(tags=["Сайты"])
preview_router = APIRouter(tags=["Предпросмотр"])


@router.get("/sites/themes", response_model=list[ThemeRead])
async def get_themes() -> list[ThemeRead]:
    return [
        ThemeRead(
            key=theme.key,
            name=theme.name,
            description=theme.description,
            accent=theme.accent,
            background=theme.background,
            ink=theme.ink,
        )
        for theme in THEMES.values()
    ]


@router.get("/sites", response_model=list[SiteRead])
async def get_sites(service: SiteServiceDep) -> list[SiteRead]:
    """Все собранные версии сайтов, новые сверху."""
    return [SiteRead.from_entity(site, revision) for site, revision in await service.recent()]


@router.post(
    "/companies/{company_id}/sites",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobRead,
)
async def build_site(
    company_id: UUID,
    data: BuildSiteRequest,
    service: SiteServiceDep,
) -> JobRead:
    """Собирает новую версию сайта из утверждённой карточки. Факты заново не генерируются."""

    if not data.reuse_texts:
        ensure_llm_configured()
    job = await service.start(
        company_id,
        language=data.language,
        theme=data.theme,
        accent=data.accent,
        reuse_texts=data.reuse_texts,
        model=resolve_text_model(data.model),
        budget=new_budget(data.budget_usd),
    )
    return JobRead.from_entity(job)


@router.get("/companies/{company_id}/sites", response_model=list[SiteRead])
async def get_company_sites(
    company_id: UUID,
    service: SiteServiceDep,
    companies: CompanyServiceDep,
) -> list[SiteRead]:
    company = await companies.get(company_id)
    return [
        SiteRead.from_entity(site, company.revision)
        for site in await service.by_company(company_id)
    ]


@router.get("/sites/{site_id}", response_model=SiteRead)
async def get_site(
    site_id: UUID,
    service: SiteServiceDep,
    companies: CompanyServiceDep,
) -> SiteRead:
    site = await service.get(site_id)
    company = await companies.get(site.company_id)
    return SiteRead.from_entity(site, company.revision)


@router.get("/sites/{site_id}/download")
async def download_site(site_id: UUID, service: SiteServiceDep) -> FileResponse:
    """Готовый сайт архивом."""

    site = await service.get(site_id)
    archive = site_archive(site.id)
    if not archive.exists():
        raise NotFoundError("Архив сайта не найден")
    domain = site.snapshot["brand"]["domain"].split(".")[0]
    return FileResponse(
        archive,
        media_type="application/zip",
        filename=f"{domain}-v{site.number}-{site.language.value}.zip",
    )


@router.delete("/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(site_id: UUID, service: SiteServiceDep) -> None:
    await service.delete(site_id)


@preview_router.get("/preview/{site_id}", include_in_schema=False)
async def preview_root(site_id: UUID) -> RedirectResponse:
    return RedirectResponse(f"/preview/{site_id}/index.html")


@preview_router.get("/preview/{site_id}/{file_path:path}", include_in_schema=False)
async def preview_file(site_id: UUID, file_path: str) -> FileResponse:
    """Предпросмотр: отдаёт файлы собранного сайта. Платных запросов не делает."""

    target = await asyncio.to_thread(_resolve_site_file, site_id, file_path)
    return FileResponse(target)


def _resolve_site_file(site_id: UUID, file_path: str) -> Path:
    root = Path(site_dir(site_id)).resolve()
    target = (root / (file_path or "index.html")).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise NotFoundError("Файл сайта не найден")
    return target
