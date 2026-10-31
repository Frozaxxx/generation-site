"""Фейковая модель: отвечает валидными черновиками и считает «стоимость»."""

import io
import itertools
import re

from PIL import Image
from pydantic import BaseModel

from src.companies.application.generation.drafts import (
    ConceptDraft,
    ProductDraft,
    ReviewDraft,
    RevisionDraft,
    TeamDraft,
)
from src.llm.domain.budget import OperationBudget
from src.llm.domain.vo import GeneratedImage, Usage
from src.sites.application.drafts import SiteCopyDraft, TranslationDraft

_counter = itertools.count(1)


def _text(prefix: str, length: int) -> str:
    base = f"{prefix}: конкретное описание рабочего процесса аналитиков и результата. "
    return (base * (length // len(base) + 1))[:length].strip()


def _german(prefix: str, length: int) -> str:
    base = f"{prefix}: konkrete Beschreibung der Arbeit von Analysten und des Ergebnisses. "
    return (base * (length // len(base) + 1))[:length].strip()


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (512, 640), (180, 160, 150)).save(buffer, format="PNG")
    return buffer.getvalue()


class FakeLLM:
    def __init__(self, review_issues: list[list[dict]] | None = None) -> None:
        self.calls: list[str] = []
        # Ответы смысловой проверки по очереди, по умолчанию замечаний нет.
        self.review_issues = list(review_issues or [])

    async def complete_json[T: BaseModel](
        self, *, schema: type[T], budget: OperationBudget, user: str = "", **_
    ):
        self.calls.append(schema.__name__)
        budget.add(Usage(model="fake", input_tokens=100, output_tokens=200, cost_usd=0.001))
        number = next(_counter)

        if issubclass(schema, ConceptDraft):
            years = sorted(
                {schema.min_year, min(schema.min_year + 2, schema.max_year), schema.max_year}
            )
            data = {
                "brand_name": f"Brightwell {chr(64 + number % 26 or 1)}",
                "tagline": "Обзоры отчётности для небольших фондов",
                "niche": _text("Ниша", 60),
                "product_name": f"Brief {number}",
                "founding_story": _text(f"История {number}", 300),
                "specialization": _text("Специализация", 200),
                "milestones": [
                    {"year": year, "title": f"Этап {year}", "description": _text("Этап", 40)}
                    for year in years
                ],
                "segments": [
                    {"name": "Фонды акций", "description": _text("Сегмент", 40)},
                    {"name": "Семейные офисы", "description": _text("Сегмент", 40)},
                ],
                "client_problem": _text("Проблема", 200),
            }
            if len(data["milestones"]) < 3:
                data["milestones"].append(dict(data["milestones"][-1]))
        elif issubclass(schema, ProductDraft):
            data = {
                "summary": _text("Продукт", 200),
                "inputs": ["Список эмитентов", "Публичные отчёты", "Стенограммы звонков"],
                "process": [
                    {"title": f"Шаг {i}", "description": _text("Шаг", 40)} for i in range(1, 5)
                ],
                "outputs": ["Обзор", "Таблица отклонений", "Ссылки на источники"],
                "limitations": ["Только ЕС", "Нет рекомендаций", "Сутки на обзор"],
                "benefits": [
                    {"title": f"Плюс {i}", "description": _text("Плюс", 40)} for i in range(1, 4)
                ],
                "delivery": _text("Поставка", 60),
                "faq": [
                    {"question": f"Вопрос номер {i}?", "answer": _text("Ответ", 60)}
                    for i in range(1, 6)
                ],
            }
            if issubclass(schema, RevisionDraft):
                data["tagline"] = "Исправленный слоган без обещаний"
        elif issubclass(schema, TeamDraft):
            data = {
                "people": [
                    {
                        "id": person_id,
                        "position": "Руководитель направления",
                        "department": "Аналитика",
                        "bio": _text("Биография", 120),
                        "experience": ["Аналитик, управляющая компания, 2012–2018"],
                        "education": "Universität Mannheim, экономика",
                    }
                    for person_id in schema.expected_ids
                ]
            }
        elif issubclass(schema, SiteCopyDraft):
            brand = schema.brand or "Brand"
            german = "Deutsch" in user
            text = _german if german else _text
            meta = {
                "title": f"{brand}: "
                + ("Berichte ohne Handarbeit" if german else "обзоры отчётности"),
                "description": text("Beschreibung der Seite für Suche und soziale Netzwerke", 140),
            }
            data = {
                "home": meta,
                "product": meta,
                "company": meta,
                "hero_title": text("Berichte ohne manuellen Abgleich", 40),
                "hero_lead": text("Einleitung", 120),
                "audience_lead": text("Zielgruppe", 60),
                "benefits_lead": text("Vorteile", 60),
                "process_lead": text("Ablauf", 60),
                "cta_title": text("So funktioniert der Service", 40),
                "cta_text": text("Aufruf", 60),
                "product_lead": text("Produkt", 80),
                "limitations_lead": text("Grenzen", 60),
                "company_lead": text("Unternehmen", 80),
                "team_lead": text("Team", 60),
            }
        elif issubclass(schema, TranslationDraft):
            # «Перевод»: немецкая фраза плюс те же числа и латинские термины, что в оригинале.
            data = {
                "items": {
                    key: " ".join(["Übersetzung", *re.findall(r"\d+|[A-Za-z][\w&+.\-]*", text)])
                    for key, text in schema.source.items()
                }
            }
        elif issubclass(schema, ReviewDraft):
            data = {"issues": self.review_issues.pop(0) if self.review_issues else []}
        else:
            raise TypeError(f"unexpected schema {schema}")

        return schema.model_validate(data)

    async def generate_image(self, *, budget: OperationBudget, **_) -> GeneratedImage:
        self.calls.append("image")
        budget.add(Usage(model="fake-image", cost_usd=0.04))
        return GeneratedImage(content=_png(), media_type="image/png")
