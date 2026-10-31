from typing import Any, Literal

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.shared.application.dtos import BaseQueryParamFilters

from ..domain.enums import CompanyScale, CompanyStatus, IssueSeverity


class CompanyFilters(BaseQueryParamFilters):
    """Фильтры списка компаний."""

    status: CompanyStatus | None = None
    scale: CompanyScale | None = None
    search: str | None = Field(default=None, max_length=80, description="Поиск по бренду.")
    sort: Literal["created_at:asc", "created_at:desc", "brand_name:asc"] = "created_at:desc"


class IssueRead(BaseModel):
    code: str
    severity: IssueSeverity
    path: str
    message: str


class CompanyListItem(BaseModel):
    """Строка библиотеки компаний."""

    id: UUID
    brand_name: str
    legal_name: str
    city: str
    service_type: str
    scale: CompanyScale
    status: CompanyStatus
    revision: int
    team_size: int
    created_at: datetime
    updated_at: datetime


class CompanyRead(BaseModel):
    """Компания целиком: параметры, карточка, сведения о генерации и проверки."""

    id: UUID
    status: CompanyStatus
    revision: int
    params: dict[str, Any]
    profile: dict[str, Any]
    generation: dict[str, Any] | None
    issues: list[IssueRead]
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None


class ProfileUpdate(BaseModel):
    """Отредактированная карточка целиком. Структура проверяется доменной схемой."""

    model_config = ConfigDict(extra="forbid")

    profile: dict[str, Any]
    revision: int = Field(ge=1, description="Ревизия, с которой начиналось редактирование.")


class GenerateCompanyRequest(BaseModel):
    """Параметры генерации. Пустое поле - случайное значение из каталога."""

    model_config = ConfigDict(extra="forbid")

    brand_name: str | None = Field(default=None, max_length=40)
    country: str | None = Field(default=None, examples=["DE"])
    direction: str | None = Field(default=None, examples=["ai_investment_research"])
    service_type: str | None = Field(default=None, examples=["earnings_analysis"])
    scale: CompanyScale | None = None
    model: str | None = Field(default=None, examples=["google/gemini-2.5-flash"])
    with_photos: bool = Field(default=True, description="Генерировать фото команды.")
    budget_usd: float | None = Field(
        default=None,
        gt=0,
        description="Лимит операции, не больше OPENROUTER_OPERATION_BUDGET_USD.",
    )


class PaidActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = None
    budget_usd: float | None = Field(default=None, gt=0)


class CatalogOption(BaseModel):
    key: str
    label: str
    description: str | None = None


class CatalogRead(BaseModel):
    """Значения для формы генерации; любое поле можно оставить случайным."""

    countries: list[CatalogOption]
    directions: list[CatalogOption]
    service_types: dict[str, list[CatalogOption]]
    scales: list[CatalogOption]
    models: list[CatalogOption]
    default_model: str
