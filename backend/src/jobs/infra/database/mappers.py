from src.shared.infra.database.mappers import ModelMapper
from src.shared.infra.database.types import aware

from ...domain.entities import Job, JobError
from ...domain.enums import JobKind, JobStatus
from .models import JobOrm


class JobMapper(ModelMapper[Job, JobOrm]):
    """Преобразует задачу между доменной сущностью и ORM-моделью."""

    @staticmethod
    def from_model(model: JobOrm) -> Job:
        return Job(
            id=model.id,
            created_at=aware(model.created_at),  # pyright: ignore[reportArgumentType]
            updated_at=aware(model.updated_at),  # pyright: ignore[reportArgumentType]
            kind=JobKind(model.kind),
            status=JobStatus(model.status),
            stages=list(model.stages),
            stage_index=model.stage_index,
            message=model.message,
            params=dict(model.params),
            subject_id=model.subject_id,
            result_id=model.result_id,
            cost_usd=model.cost_usd,
            budget_usd=model.budget_usd,
            requests=model.requests,
            error=JobError(**model.error) if model.error else None,
            started_at=aware(model.started_at),
            finished_at=aware(model.finished_at),
        )

    @staticmethod
    def to_model(entity: Job) -> JobOrm:
        return JobOrm(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            kind=entity.kind.value,
            status=entity.status.value,
            stages=entity.stages,
            stage_index=entity.stage_index,
            message=entity.message[:500],
            params=entity.params,
            subject_id=entity.subject_id,
            result_id=entity.result_id,
            cost_usd=entity.cost_usd,
            budget_usd=entity.budget_usd,
            requests=entity.requests,
            error=(
                {
                    "code": entity.error.code,
                    "message": entity.error.message,
                    "details": entity.error.details,
                }
                if entity.error
                else None
            ),
            started_at=entity.started_at,
            finished_at=entity.finished_at,
        )
