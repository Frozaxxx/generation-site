from typing import Protocol

from uuid import UUID

from ..domain.entities import Entity
from .dtos import BaseQueryParamFilters, Page, Pagination


class Repository[EntityT: Entity](Protocol):
    async def create(self, entity: EntityT) -> EntityT: ...

    async def read(self, uid: UUID) -> EntityT | None: ...

    async def find(
        self,
        pagination: Pagination,
        filters: BaseQueryParamFilters | None = None,
    ) -> Page[EntityT]: ...

    async def upsert(self, entity: EntityT) -> None: ...

    async def delete(self, uid: UUID) -> None: ...
