from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from src.shared.application.dtos import Page
from src.shared.dependencies import PaginationDep

from ...application.catalog import build_catalog
from ...application.dtos import (
    CatalogRead,
    CompanyFilters,
    CompanyListItem,
    CompanyRead,
    ProfileUpdate,
)
from ...application.mappers import to_export, to_list_item, to_read
from ...dependencies import CompanyServiceDep

router = APIRouter(tags=["Компании"])


@router.get("/catalog", response_model=CatalogRead)
async def get_catalog() -> CatalogRead:
    """Справочник параметров генерации."""
    return build_catalog()


@router.get("/companies", response_model=Page[CompanyListItem])
async def get_companies(
    service: CompanyServiceDep,
    pagination: PaginationDep,
    filters: Annotated[CompanyFilters, Query()],
) -> Page[CompanyListItem]:
    """Библиотека созданных компаний."""

    page = await service.find(pagination, filters)
    return Page.create(
        items=[to_list_item(company) for company in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
    )


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
async def delete_company(company_id: UUID, service: CompanyServiceDep) -> None:
    await service.delete(company_id)


@router.get("/companies/{company_id}/export")
async def export_company(company_id: UUID, service: CompanyServiceDep) -> JSONResponse:
    """Скачивание данных компании в JSON."""

    company = await service.get(company_id)
    filename = f"{company.profile.brand.domain.split('.')[0]}-r{company.revision}.json"
    return JSONResponse(
        content=to_export(company),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
