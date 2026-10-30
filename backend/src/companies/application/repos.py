from typing import Protocol

from uuid import UUID

from src.shared.application.dtos import Page, Pagination

from ..domain.entities import Company
from .dtos import CompanyFilters


class CompanyRepository(Protocol):
    """Операции хранения, необходимые для компаний."""

    async def create(self, entity: Company) -> Company: ...

    async def read(self, uid: UUID) -> Company | None: ...

    async def upsert(self, entity: Company) -> None: ...

    async def delete(self, uid: UUID) -> None: ...

    async def find(
        self,
        pagination: Pagination,
        filters: CompanyFilters | None = None,
    ) -> Page[Company]: ...
