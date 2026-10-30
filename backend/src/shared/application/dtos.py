from typing import Any, Literal, Self

from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt


class Pagination(BaseModel):
    """Параметры пагинации, которые приходят от клиента (query config)."""

    page: PositiveInt = Field(default=1, ge=1, description="Номер страницы, начинается с 1")
    size: PositiveInt = Field(
        default=20, ge=1, le=100, description="Размер страницы (количество элементов на странице)."
    )

    @property
    def offset(self) -> int:
        """Смещение пагинации"""

        return (self.page - 1) * self.size


class Page[T: Any](BaseModel):
    """Полная страница с элементами."""

    page: PositiveInt = Field(..., description="Текущий номер страницы")
    size: PositiveInt = Field(..., description="Количество элементов на странице")
    total: NonNegativeInt = Field(..., description="Всего элементов на сервере")
    items: list[T] = Field(default_factory=list)

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> Self:
        return cls(items=items, total=total, page=page, size=size)


class BaseQueryParamFilters(BaseModel):
    """Базовые фильтры списков."""

    sort: Literal["created_at:asc", "created_at:desc"] = "created_at:desc"
