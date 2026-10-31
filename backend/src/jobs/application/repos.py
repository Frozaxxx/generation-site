from typing import Protocol

from uuid import UUID

from src.shared.application.dtos import Page, Pagination

from ..domain.entities import Job
from .dtos import JobFilters


class JobRepository(Protocol):
    async def create(self, entity: Job) -> Job: ...

    async def read(self, uid: UUID) -> Job | None: ...

    async def upsert(self, entity: Job) -> None: ...

    async def find(
        self, pagination: Pagination, filters: JobFilters | None = None
    ) -> Page[Job]: ...

    async def fail_unfinished(self, message: str) -> int: ...
