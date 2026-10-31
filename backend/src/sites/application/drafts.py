from typing import ClassVar, Self

import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .texts import latin_terms, numbers

_DIGITS_RE = re.compile(r"\d+")


class _Draft(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class PageMeta(_Draft):
    title: str = Field(min_length=10, max_length=70, description="title страницы, до 60 символов")
    description: str = Field(
        min_length=70, max_length=180, description="meta description, 120–160 символов"
    )


class SiteCopyDraft(_Draft):
    """Подача текста сайта. Факты в ней не придумываются: только числа из карточки."""

    allowed_numbers: ClassVar[frozenset[str]] = frozenset()
    brand: ClassVar[str] = ""

    home: PageMeta
    product: PageMeta
    company: PageMeta
    hero_title: str = Field(min_length=10, max_length=90)
    hero_lead: str = Field(min_length=60, max_length=320)
    audience_lead: str = Field(min_length=30, max_length=260)
    benefits_lead: str = Field(min_length=30, max_length=260)
    process_lead: str = Field(min_length=30, max_length=260)
    cta_title: str = Field(min_length=10, max_length=90)
    cta_text: str = Field(min_length=30, max_length=260)
    product_lead: str = Field(min_length=40, max_length=320)
    limitations_lead: str = Field(min_length=30, max_length=260)
    company_lead: str = Field(min_length=40, max_length=320)
    team_lead: str = Field(min_length=30, max_length=260)

    @model_validator(mode="after")
    def _brand_in_titles(self) -> Self:
        """Бренд в title каждой страницы: по названию компании сайт должен находиться."""

        if not self.brand:
            return self
        missing = [
            name
            for name, meta in (
                ("home", self.home),
                ("product", self.product),
                ("company", self.company),
            )
            if self.brand.lower() not in meta.title.lower()
        ]
        if missing:
            raise ValueError(
                f"В title страниц {', '.join(missing)} нет названия бренда «{self.brand}»"
            )
        return self

    @model_validator(mode="after")
    def _no_invented_numbers(self) -> Self:
        if not self.allowed_numbers:
            return self
        invented: set[str] = set()
        for value in self.model_dump().values():
            texts = value.values() if isinstance(value, dict) else [value]
            for text in texts:
                invented.update(
                    number
                    for number in _DIGITS_RE.findall(str(text))
                    if number not in self.allowed_numbers
                )
        if invented:
            raise ValueError(
                "В тексте числа, которых нет в карточке компании: "
                f"{', '.join(sorted(invented))}. Убери их или используй только факты карточки"
            )
        return self

    @classmethod
    def with_facts(cls, allowed: set[str], brand: str = "") -> type[SiteCopyDraft]:
        return type(cls.__name__, (cls,), {"allowed_numbers": frozenset(allowed), "brand": brand})


class TranslationDraft(_Draft):
    """Перевод текстов по путям. Проверяет, что смысл и факты не потерялись."""

    source: ClassVar[dict[str, str]] = {}

    items: dict[str, str]

    @model_validator(mode="after")
    def _same_facts(self) -> Self:
        missing = sorted(set(self.source) - set(self.items))
        if missing:
            raise ValueError(f"Нет переводов для ключей: {', '.join(missing[:10])}")

        problems = []
        for key, original in self.source.items():
            translated = self.items[key]
            if not translated.strip():
                problems.append(f"{key}: пустой перевод")
                continue
            if numbers(original) != numbers(translated):
                problems.append(
                    f"{key}: числа не совпадают с оригиналом ({', '.join(numbers(original))})"
                )
            lost = latin_terms(original) - latin_terms(translated)
            if lost:
                problems.append(f"{key}: потеряны имена или термины: {', '.join(sorted(lost))}")
        if problems:
            raise ValueError("; ".join(problems[:10]))

        self.items = {key: self.items[key] for key in self.source}
        return self

    @classmethod
    def for_texts(cls, source: dict[str, str]) -> type[TranslationDraft]:
        return type(cls.__name__, (cls,), {"source": dict(source)})
