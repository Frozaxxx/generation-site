"""
Служебные команды: `python -m src.cli <команда>`.
"""

import argparse
import asyncio
import json
import sys

from pydantic import BaseModel, Field

from src.companies.domain.serialization import profile_json_schema
from src.core.settings import DOCS_DIR, openrouter_config, storage_config
from src.llm.dependencies import ensure_llm_configured, new_budget, resolve_text_model
from src.llm.infra.openrouter import OpenRouterClient

SCHEMA_FILE = DOCS_DIR / "company.schema.json"


def _print(text: str) -> None:
    sys.stdout.write(text + "\n")


def export_schema(_args: argparse.Namespace) -> None:
    """Сохраняет JSON Schema карточки компании в docs/."""

    SCHEMA_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_FILE.write_text(
        json.dumps(profile_json_schema(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _print(f"Схема сохранена: {SCHEMA_FILE}")


class _CheckAnswer(BaseModel):
    city: str = Field(description="Город в Германии")
    area_code: str = Field(description="Телефонный код города без нуля")
    fact: str = Field(min_length=10, description="Короткий факт о деловой жизни города")


async def _check_openrouter(args: argparse.Namespace) -> None:
    ensure_llm_configured()
    model = resolve_text_model(args.model)
    budget = new_budget(min(0.2, openrouter_config.operation_budget_usd))
    client = OpenRouterClient(openrouter_config)

    try:
        answer = await client.complete_json(
            model=model,
            system="Отвечай строго JSON-объектом по схеме.",
            user="Назови один крупный финансовый город Германии.",
            schema=_CheckAnswer,
            budget=budget,
            max_tokens=300,
        )
        _print(f"Модель: {model}")
        _print(f"Ответ:  {answer.model_dump_json()}")

        if args.image:
            image = await client.generate_image(
                model=openrouter_config.image_model,
                prompt=(
                    "Candid office portrait of a 40-year-old German product manager, natural "
                    "window light, 50mm lens, shallow depth of field, realistic skin texture"
                ),
                budget=budget,
            )
            path = storage_config.data_dir / f"check-portrait.{image.extension}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(image.content)
            _print(f"Фото:   {path} ({len(image.content) // 1024} КБ)")
    finally:
        await client.aclose()

    _print(
        f"Запросов: {budget.requests}, токены {budget.input_tokens}/{budget.output_tokens}, "
        f"стоимость ${budget.spent_usd:.5f}"
    )


def check_openrouter(args: argparse.Namespace) -> None:
    """Один дешёвый запрос к OpenRouter: проверка ключа, модели и учёта стоимости."""

    asyncio.run(_check_openrouter(args))


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m src.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("export-schema", help="Выгрузить JSON Schema карточки в docs/")

    check = commands.add_parser("check-openrouter", help="Проверить ключ и модель OpenRouter")
    check.add_argument("--model", default=None, help="Модель из OPENROUTER_ALLOWED_TEXT_MODELS")
    check.add_argument("--image", action="store_true", help="Сгенерировать тестовое фото")

    args = parser.parse_args()
    {"export-schema": export_schema, "check-openrouter": check_openrouter}[args.command](args)


if __name__ == "__main__":
    main()
