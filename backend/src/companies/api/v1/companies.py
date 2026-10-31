from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from src.jobs.application.dtos import JobRead
from src.llm.dependencies import ensure_llm_configured, new_budget, resolve_text_model
from src.shared.application.dtos import Page
from src.shared.dependencies import DBSession, PaginationDep

from ...application.catalog import build_catalog
from ...application.dtos import (
    CatalogRead,
    CompanyFilters,
    CompanyListItem,
    CompanyRead,
    GenerateCompanyRequest,
    PaidActionRequest,
    ProfileUpdate,
)
from ...application.generation.facts import GenerationRequest
from ...application.mappers import to_export, to_list_item, to_read
from ...dependencies import CompanyAIServiceDep, CompanyGenerationServiceDep, CompanyServiceDep

router = APIRouter(tags=["Компании"])


@router.get("/catalog", response_model=CatalogRead)
async def get_catalog() -> CatalogRead:
    """Справочник параметров генерации."""
    return build_catalog()


@router.get("/companies", response_model=Page[CompanyListItem])
async def get_companies(
    service: CompanyServiceDep,
    session: DBSession,
    pagination: PaginationDep,
    filters: Annotated[CompanyFilters, Query()],
) -> Page[CompanyListItem]:
    """Библиотека созданных компаний."""

    from src.sites.infra.database.repos.sites import SqlSiteVersionRepository  # noqa: PLC0415

    page = await service.find(pagination, filters)
    counts = await SqlSiteVersionRepository(session).counts_by_company()
    return Page.create(
        items=[
            to_list_item(company).model_copy(update={"sites_count": counts.get(company.id, 0)})
            for company in page.items
        ],
        total=page.total,
        page=page.page,
        size=page.size,
    )


@router.post(
    "/companies/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobRead,
)
async def generate_company(
    data: GenerateCompanyRequest,
    service: CompanyGenerationServiceDep,
) -> JobRead:
    """Запускает генерацию компании в фоне. Прогресс - `GET /jobs/{id}`."""

    ensure_llm_configured()
    request = GenerationRequest(
        brand_name=data.brand_name,
        country=data.country,
        direction=data.direction,
        service_type=data.service_type,
        scale=data.scale,
        model=resolve_text_model(data.model) if data.model else None,
        with_photos=data.with_photos,
        custom_direction=data.custom_direction,
        custom_service=data.custom_service,
    )
    job = await service.start(request, new_budget(data.budget_usd))
    return JobRead.from_entity(job)


@router.post("/companies/{company_id}/review", response_model=CompanyRead)
async def review_company(
    company_id: UUID,
    data: PaidActionRequest,
    service: CompanyAIServiceDep,
) -> CompanyRead:
    """Платная смысловая проверка текущей ревизии карточки моделью."""

    ensure_llm_configured()
    company = await service.review(
        company_id, resolve_text_model(data.model), new_budget(data.budget_usd)
    )
    return to_read(company)


@router.post("/companies/{company_id}/team/{person_id}/photo", response_model=CompanyRead)
async def regenerate_photo(
    company_id: UUID,
    person_id: str,
    data: PaidActionRequest,
    service: CompanyAIServiceDep,
) -> CompanyRead:
    """Создаёт новое фото сотрудника (платно). Факты карточки не меняются."""

    ensure_llm_configured()
    company = await service.regenerate_photo(company_id, person_id, new_budget(data.budget_usd))
    return to_read(company)


@router.get("/companies/{company_id}", response_model=CompanyRead)
async def get_company(company_id: UUID, service: CompanyServiceDep) -> CompanyRead:
    """Карточка компании вместе с результатами проверок. Платных запросов не делает."""
    return to_read(await service.get(company_id))


@router.put("/companies/{company_id}/profile", response_model=CompanyRead)
async def update_profile(
    company_id: UUID,
    data: ProfileUpdate,
    service: CompanyServiceDep,
) -> CompanyRead:
    """Сохраняет ручные правки карточки. После правок карточка снова черновик."""

    company, issues = await service.edit_profile(
        company_id, data=data.profile, revision=data.revision
    )
    return to_read(company, issues)


@router.post("/companies/{company_id}/approve", response_model=CompanyRead)
async def approve_company(company_id: UUID, service: CompanyServiceDep) -> CompanyRead:
    """Утверждает карточку, если проверки не нашли ошибок."""
    return to_read(await service.approve(company_id))


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: UUID,
    service: CompanyServiceDep,
    session: DBSession,
) -> None:
    """Удаляет компанию, её версии сайтов и файлы (фото, собранные сайты)."""

    # Импорт здесь: модуль sites сам зависит от companies.
    from src.sites.application.service import remove_site_files  # noqa: PLC0415
    from src.sites.infra.database.repos.sites import SqlSiteVersionRepository  # noqa: PLC0415

    sites = await SqlSiteVersionRepository(session).by_company(company_id)
    await service.delete(company_id)
    for site in sites:
        remove_site_files(site.id)


@router.get("/companies/{company_id}/export")
async def export_company(company_id: UUID, service: CompanyServiceDep) -> JSONResponse:
    """Скачивание данных компании в JSON."""

    company = await service.get(company_id)
    filename = f"{company.profile.brand.domain.split('.')[0]}-r{company.revision}.json"
    return JSONResponse(
        content=to_export(company),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
