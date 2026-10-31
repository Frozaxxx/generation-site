"""
Схемы ответов модели. Ограничения (количество, годы, id людей) проверяются здесь,
поэтому невалидный ответ уходит модели на исправление, а не в карточку.
"""

from typing import ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ...domain.catalog.trademarks import find_known_brand
from ...domain.constants import FAQ_SIZE, MAX_BIO_LENGTH, MIN_BIO_LENGTH


class _Draft(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class MilestoneDraft(_Draft):
    year: int
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=20, max_length=700)


class SegmentDraft(_Draft):
    name: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=20, max_length=700)


class ConceptDraft(_Draft):
    """История, позиционирование и аудитория."""

    min_year: ClassVar[int] = 1990
    max_year: ClassVar[int] = 2100

    brand_name: str = Field(
        min_length=2,
        max_length=40,
        pattern=r"^[A-Za-zÄÖÜäöü][A-Za-z0-9ÄÖÜäöüß&\- ]*$",
        description="Латиница, без правовой формы",
    )
    tagline: str = Field(min_length=10, max_length=160)
    niche: str = Field(
        min_length=20, max_length=450, description="Суть специализации одной фразой"
    )
    product_name: str = Field(min_length=2, max_length=60)
    founding_story: str = Field(min_length=200, max_length=3000)
    specialization: str = Field(min_length=150, max_length=2500)
    milestones: list[MilestoneDraft] = Field(min_length=3, max_length=5)
    segments: list[SegmentDraft] = Field(min_length=2, max_length=4)
    client_problem: str = Field(min_length=150, max_length=2000)

    @field_validator("brand_name")
    @classmethod
    def _no_legal_form(cls, value: str) -> str:
        if any(form in value.split() for form in ("GmbH", "AG", "UG", "KG")):
            raise ValueError("brand_name не должен содержать правовую форму")
        if known := find_known_brand(value):
            raise ValueError(f"brand_name содержит реальный бренд «{known}», придумай другое")
        return value

    @model_validator(mode="after")
    def _years(self) -> Self:
        years = [milestone.year for milestone in self.milestones]
        if years[0] != self.min_year:
            raise ValueError(f"Первый этап должен быть годом основания: {self.min_year}")
        if any(not self.min_year <= year <= self.max_year for year in years):
            raise ValueError(
                f"Годы этапов должны быть в диапазоне {self.min_year}–{self.max_year}"
            )
        if years != sorted(years):
            raise ValueError("Этапы должны идти по возрастанию лет")
        return self

    @classmethod
    def bounded(cls, founded_year: int, current_year: int) -> type[ConceptDraft]:
        return type(cls.__name__, (cls,), {"min_year": founded_year, "max_year": current_year})


class StepDraft(_Draft):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=20, max_length=700)


class BenefitDraft(_Draft):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=20, max_length=700)


class FaqDraft(_Draft):
    question: str = Field(min_length=10, max_length=250)
    answer: str = Field(min_length=30, max_length=1200)


class ProductDraft(_Draft):
    summary: str = Field(min_length=150, max_length=2500)
    inputs: list[str] = Field(min_length=3, max_length=6)
    process: list[StepDraft] = Field(min_length=4, max_length=6)
    outputs: list[str] = Field(min_length=3, max_length=6)
    limitations: list[str] = Field(min_length=3, max_length=6)
    benefits: list[BenefitDraft] = Field(min_length=3, max_length=4)
    delivery: str = Field(min_length=40, max_length=1000)
    faq: list[FaqDraft] = Field(min_length=FAQ_SIZE, max_length=FAQ_SIZE)


class RevisionDraft(ProductDraft):
    """Исправленное описание продукта и слоган после смысловой проверки."""

    tagline: str = Field(min_length=10, max_length=160)


class PersonDraft(_Draft):
    id: str
    position: str = Field(min_length=3, max_length=150)
    department: str | None = Field(default=None, max_length=100)
    bio: str = Field(min_length=MIN_BIO_LENGTH, max_length=MAX_BIO_LENGTH)
    experience: list[str] = Field(min_length=1, max_length=4)
    education: str = Field(min_length=5, max_length=300)


class TeamDraft(_Draft):
    expected_ids: ClassVar[tuple[str, ...]] = ()

    people: list[PersonDraft]

    @model_validator(mode="after")
    def _same_people(self) -> Self:
        ids = [person.id for person in self.people]
        if sorted(ids) != sorted(self.expected_ids):
            raise ValueError(
                f"Нужны ровно эти id в любом порядке: {', '.join(self.expected_ids)}; "
                f"получены: {', '.join(ids)}"
            )
        return self

    @classmethod
    def for_people(cls, ids: list[str]) -> type[TeamDraft]:
        return type(cls.__name__, (cls,), {"expected_ids": tuple(ids)})


class ReviewIssueDraft(_Draft):
    path: str = Field(description="Раздел карточки, например product.limitations")
    severity: Literal["error", "warning"]
    message: str = Field(min_length=10, max_length=600)


class ReviewDraft(_Draft):
    issues: list[ReviewIssueDraft] = Field(default_factory=list, max_length=10)
