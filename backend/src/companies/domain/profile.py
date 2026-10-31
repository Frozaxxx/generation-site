"""
Карточка компании - единый источник фактов для всех страниц сайта.

Структуры описаны обычными dataclass, а валидация и JSON Schema строятся через
`pydantic.TypeAdapter`, поэтому домен не зависит от слоя API.
"""

from typing import Annotated, Literal

from dataclasses import dataclass, field

from pydantic import Field

from .constants import MAX_BIO_LENGTH, MIN_BIO_LENGTH
from .enums import Gender, TeamRole

SCHEMA_VERSION = 1

Text = Annotated[str, Field(min_length=1)]
ShortText = Annotated[str, Field(min_length=1, max_length=160)]
Paragraph = Annotated[str, Field(min_length=40, max_length=3000)]
Year = Annotated[int, Field(ge=1990, le=2100)]


@dataclass(kw_only=True)
class Brand:
    """Название бренда и юридического лица."""

    name: Annotated[str, Field(min_length=2, max_length=60, description="Название бренда.")]
    legal_form: Annotated[str, Field(description="Правовая форма: GmbH, UG, AG.")]
    legal_name: Annotated[
        str,
        Field(description="Полное наименование юрлица, например «Kestrel Data GmbH»."),
    ]
    tagline: Annotated[ShortText, Field(description="Короткое позиционирование, одна фраза.")]
    domain: Annotated[
        str,
        Field(
            pattern=r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9-]+)*\.[a-z]{2,}$",
            description="Домен сайта без протокола.",
        ),
    ]


@dataclass(kw_only=True)
class Address:
    street: ShortText
    house_number: Annotated[str, Field(pattern=r"^\d{1,4}[a-zA-Z]?$")]
    postal_code: Annotated[str, Field(pattern=r"^\d{5}$")]
    city: ShortText
    district: ShortText | None = None
    state: ShortText
    country_code: Annotated[str, Field(pattern=r"^[A-Z]{2}$")]

    @property
    def street_line(self) -> str:
        return f"{self.street} {self.house_number}"

    @property
    def city_line(self) -> str:
        return f"{self.postal_code} {self.city}"


@dataclass(kw_only=True)
class Contacts:
    address: Address
    city_key: Annotated[str, Field(description="Ключ города из каталога страны.")]
    phone: Annotated[
        str,
        Field(pattern=r"^\+\d{8,15}$", description="Телефон в формате E.164."),
    ]
    phone_display: Annotated[str, Field(description="Телефон в местном формате записи.")]
    email: Annotated[str, Field(pattern=r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")]
    office_hours: ShortText


@dataclass(kw_only=True)
class Milestone:
    year: Year
    title: ShortText
    description: Text


@dataclass(kw_only=True)
class History:
    founded_year: Year
    employees: Annotated[int, Field(ge=1, le=10_000)]
    founding_story: Annotated[Paragraph, Field(description="Как и почему появилась компания.")]
    specialization: Annotated[
        Paragraph, Field(description="В чём компания сильна и что не делает.")
    ]
    milestones: Annotated[list[Milestone], Field(min_length=2, max_length=8)]


@dataclass(kw_only=True)
class AudienceSegment:
    name: ShortText
    description: Text


@dataclass(kw_only=True)
class Audience:
    segments: Annotated[list[AudienceSegment], Field(min_length=2, max_length=5)]
    client_problem: Annotated[Paragraph, Field(description="Проблема клиента до сервиса.")]


@dataclass(kw_only=True)
class ProcessStep:
    title: ShortText
    description: Text


@dataclass(kw_only=True)
class Benefit:
    title: ShortText
    description: Text


@dataclass(kw_only=True)
class Product:
    name: Annotated[str, Field(min_length=2, max_length=80)]
    summary: Paragraph
    inputs: Annotated[list[Text], Field(min_length=2, description="Какие данные нужны на входе.")]
    process: Annotated[list[ProcessStep], Field(min_length=3, max_length=6)]
    outputs: Annotated[list[Text], Field(min_length=2, description="Что клиент получает.")]
    limitations: Annotated[
        list[Text],
        Field(min_length=2, description="Чего сервис не делает и где его границы."),
    ]
    benefits: Annotated[list[Benefit], Field(min_length=3, max_length=4)]
    delivery: Annotated[Text, Field(description="Формат и сроки поставки результата.")]


@dataclass(kw_only=True)
class Photo:
    file: Annotated[str, Field(description="Путь к файлу относительно папки медиа компании.")]
    alt: ShortText


@dataclass(kw_only=True)
class Person:
    id: Annotated[str, Field(pattern=r"^[a-z0-9-]+$", description="Стабильный slug человека.")]
    first_name: ShortText
    last_name: ShortText
    gender: Gender
    age: Annotated[int, Field(ge=22, le=75)]
    role: TeamRole
    position: Annotated[ShortText, Field(description="Должность в том виде, как на сайте.")]
    department: ShortText | None = None
    bio: Annotated[str, Field(min_length=MIN_BIO_LENGTH, max_length=MAX_BIO_LENGTH)]
    experience: Annotated[list[Text], Field(min_length=1, max_length=5)]
    education: Text
    photo: Photo | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass(kw_only=True)
class FaqItem:
    question: Text
    answer: Text


@dataclass(kw_only=True)
class CompanyProfile:
    schema_version: Literal[1] = SCHEMA_VERSION
    content_language: Literal["ru"] = "ru"

    brand: Brand
    contacts: Contacts
    history: History
    audience: Audience
    product: Product
    team: Annotated[list[Person], Field(min_length=1)]
    faq: list[FaqItem] = field(default_factory=list)

    @property
    def ceo(self) -> Person | None:
        return next((person for person in self.team if person.role is TeamRole.CEO), None)

    @property
    def department_heads(self) -> list[Person]:
        return [person for person in self.team if person.role is TeamRole.DEPARTMENT_HEAD]

    def person(self, person_id: str) -> Person | None:
        return next((person for person in self.team if person.id == person_id), None)
