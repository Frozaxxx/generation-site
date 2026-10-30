# pyright: reportArgumentType=false
from typing import Any

from collections.abc import Callable
from uuid import UUID

from sqlalchemy import ColumnElement, Select, UnaryExpression, asc, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base
from src.shared.application.dtos import BaseQueryParamFilters, Page, Pagination
from src.shared.domain.entities import Entity
from src.shared.infra.database.mappers import ModelMapper


def _parse_sort_param(
    sort: str,
) -> tuple[str, Callable[[ColumnElement[Any]], UnaryExpression[Any]]]:
    """
    Парсит строку сортировки и возвращает кортеж (имя_поля, функция_сортировки).
    Поддерживает форматы "field:asc"/"field:desc" и "-field"/"field".
    """

    if ":" in sort:
        field_name, direction = sort.split(":", maxsplit=1)
        return field_name, asc if direction.lower() == "asc" else desc

    if sort.startswith("-"):
        return sort[1:], desc

    return sort, asc


def apply_sorting[ModelT: Base](
    stmt: Select[tuple[ModelT]],
    model: type[ModelT],
    sort: str | None = None,
) -> Select[tuple[ModelT]]:
    """Динамически накладывает order_by на основе параметров из фильтра."""

    if sort is None:
        return stmt.order_by(model.created_at)

    field_name, sort_func = _parse_sort_param(sort)
    if (column := getattr(model, field_name, None)) is None:
        raise ValueError(f"Invalid sort query param - '{sort}'")

    return stmt.order_by(sort_func(column))


async def paginate[ModelT: Base, ItemT](
    session: AsyncSession,
    model: type[ModelT],
    stmt: Select[tuple[ModelT]],
    pagination: Pagination,
    *,
    mapper: Callable[[ModelT], ItemT],
    sort: str | None = "created_at:desc",
) -> Page[ItemT]:
    count_stmt = select(func.count()).select_from(stmt.subquery())

    if not (total := await session.scalar(count_stmt)):
        return Page.create([], 0, pagination.page, pagination.size)

    stmt = apply_sorting(stmt, model, sort=sort)
    stmt = stmt.offset(pagination.offset).limit(pagination.size)

    results = await session.execute(stmt)

    return Page.create(
        items=[mapper(item) for item in results.scalars().all()],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


class SqlAlchemyRepository[EntityT: Entity, ModelT: Base]:
    model: type[ModelT]
    model_mapper: type[ModelMapper[EntityT, ModelT]]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: EntityT) -> EntityT:
        model = self.model_mapper.to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return entity

    async def read(self, uid: UUID) -> EntityT | None:
        model = await self._session.get(self.model, uid)
        return None if model is None else self.model_mapper.from_model(model)

    async def find(
        self,
        pagination: Pagination,
        filters: BaseQueryParamFilters | None = None,
    ) -> Page[EntityT]:
        """Для расширения логики фильтрации можно переопределить в дочерних классах."""

        return await paginate(
            session=self._session,
            model=self.model,
            stmt=select(self.model),
            pagination=pagination,
            mapper=self.model_mapper.from_model,
            sort=filters.sort if filters else None,
        )

    async def upsert(self, entity: EntityT) -> None:
        await self._session.merge(self.model_mapper.to_model(entity))
        await self._session.flush()

    async def delete(self, uid: UUID) -> None:
        await self._session.execute(delete(self.model).where(self.model.id == uid))
