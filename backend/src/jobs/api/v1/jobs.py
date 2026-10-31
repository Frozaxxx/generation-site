from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Query

from src.shared.application.dtos import Page
from src.shared.dependencies import PaginationDep
from src.shared.domain.exceptions import NotFoundError

from ...application.dtos import JobFilters, JobRead
from ...dependencies import JobRepoDep

router = APIRouter(prefix="/jobs", tags=["Задачи генерации"])


@router.get("", response_model=Page[JobRead])
async def get_jobs(
    repo: JobRepoDep,
    pagination: PaginationDep,
    filters: Annotated[JobFilters, Query()],
) -> Page[JobRead]:
    page = await repo.find(pagination, filters)
    return Page.create(
        items=[JobRead.from_entity(job) for job in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: UUID, repo: JobRepoDep) -> JobRead:
    """Текущий этап и расходы задачи. Панель опрашивает эту ручку."""

    job = await repo.read(job_id)
    if job is None:
        raise NotFoundError(f"Задача {job_id} не найдена")
    return JobRead.from_entity(job)
