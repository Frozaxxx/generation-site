from sqlalchemy import select, update

from src.shared.application.dtos import Page, Pagination
from src.shared.infra.database.repos.sqlalchemy import SqlAlchemyRepository, paginate
from src.shared.utils.time import current_datetime

from ....application.dtos import JobFilters
from ....domain.entities import Job
from ....domain.enums import JobStatus
from ..mappers import JobMapper
from ..models import JobOrm


class SqlJobRepository(SqlAlchemyRepository[Job, JobOrm]):
    model = JobOrm
    model_mapper = JobMapper

    async def find(self, pagination: Pagination, filters: JobFilters | None = None) -> Page[Job]:
        stmt = select(self.model)

        if filters:
            if filters.kind is not None:
                stmt = stmt.where(self.model.kind == filters.kind.value)
            if filters.status is not None:
                stmt = stmt.where(self.model.status == filters.status.value)
            if filters.subject_id is not None:
                stmt = stmt.where(self.model.subject_id == filters.subject_id)

        return await paginate(
            session=self._session,
            model=self.model,
            stmt=stmt,
            pagination=pagination,
            mapper=self.model_mapper.from_model,
            sort=filters.sort if filters else "created_at:desc",
        )

    async def fail_unfinished(self, message: str) -> int:
        """Задачи живут в процессе сервера: после перезапуска незавершённые уже не продолжатся."""

        result = await self._session.execute(
            update(self.model)
            .where(self.model.status.in_([JobStatus.QUEUED.value, JobStatus.RUNNING.value]))
            .values(
                status=JobStatus.FAILED.value,
                error={"code": "INTERRUPTED", "message": message, "details": {}},
                finished_at=current_datetime(),
            )
        )
        return result.rowcount  # pyright: ignore[reportAttributeAccessIssue]
