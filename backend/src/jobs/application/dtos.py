from typing import Any, Literal

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.shared.application.dtos import BaseQueryParamFilters

from ..domain.entities import Job
from ..domain.enums import JobKind, JobStatus


class JobFilters(BaseQueryParamFilters):
    kind: JobKind | None = None
    status: JobStatus | None = None
    subject_id: UUID | None = None
    sort: Literal["created_at:asc", "created_at:desc"] = "created_at:desc"


class JobErrorRead(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | list[Any]


class JobRead(BaseModel):
    """Состояние задачи для панели: этап, прогресс, расходы."""

    id: UUID
    kind: JobKind
    status: JobStatus
    stages: list[str]
    stage: str | None
    stage_index: int
    progress: float
    message: str
    subject_id: UUID | None
    result_id: UUID | None
    cost_usd: float
    budget_usd: float
    requests: int
    error: JobErrorRead | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def from_entity(cls, job: Job) -> JobRead:
        return cls(
            id=job.id,
            kind=job.kind,
            status=job.status,
            stages=job.stages,
            stage=job.stage,
            stage_index=job.stage_index,
            progress=job.progress,
            message=job.message,
            subject_id=job.subject_id,
            result_id=job.result_id,
            cost_usd=job.cost_usd,
            budget_usd=job.budget_usd,
            requests=job.requests,
            error=(
                JobErrorRead(
                    code=job.error.code,
                    message=job.error.message,
                    details=job.error.details,
                )
                if job.error
                else None
            ),
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )
