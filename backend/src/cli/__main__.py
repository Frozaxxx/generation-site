"""
Служебные команды: `python -m src.cli <команда>`.
"""

import argparse
import asyncio
import json
import logging
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


async def _generate_company(args: argparse.Namespace) -> None:
    # Импорты здесь, чтобы export-schema не тянул базу и фоновые задачи.
    from src.companies.application.generation.facts import GenerationRequest  # noqa: PLC0415
    from src.companies.application.generation.pipeline import (  # noqa: PLC0415
        STAGE_LABELS,
        CompanyGenerator,
    )
    from src.companies.application.generation.service import (  # noqa: PLC0415
        CompanyGenerationService,
    )
    from src.companies.domain.enums import CompanyScale  # noqa: PLC0415
    from src.core.database import session_factory  # noqa: PLC0415
    from src.core.migrations import upgrade_database  # noqa: PLC0415
    from src.jobs.application.runner import JobRunner  # noqa: PLC0415
    from src.jobs.infra.database.repos.jobs import SqlJobRepository  # noqa: PLC0415

    ensure_llm_configured()
    # Повторы и замечания видны в задаче, в терминал - только её этапы.
    logging.basicConfig(level=logging.ERROR)
    storage_config.media_dir.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(upgrade_database)

    client = OpenRouterClient(openrouter_config)
    runner = JobRunner(session_factory)
    service = CompanyGenerationService(runner, CompanyGenerator(client, session_factory))
    request = GenerationRequest(
        brand_name=args.brand,
        scale=CompanyScale(args.scale) if args.scale else None,
        service_type=args.service_type,
        model=resolve_text_model(args.model) if args.model else None,
        with_photos=not args.no_photos,
    )
    job = await service.start(request, new_budget())
    _print(f"Задача {job.id}")

    last = None
    while True:
        async with session_factory() as session:
            current = await SqlJobRepository(session).read(job.id)
        if current is not None:
            line = f"[{current.stage or '-'}] {current.message} · ${current.cost_usd:.4f}"
            if line != last:
                _print(line)
                last = line
            if current.status.is_finished:
                break
        await asyncio.sleep(1)

    await runner.wait_all()
    await client.aclose()

    if current.error:
        _print(f"Ошибка: {current.error.code} - {current.error.message}")
        if isinstance(current.error.details, dict) and current.error.details.get("reason"):
            _print(f"Причина: {current.error.details['reason']}")
        return
    _print(f"Компания: {current.result_id}")
    _print(f"Этапы: {', '.join(STAGE_LABELS[stage] for stage in current.stages)}")
    _print(f"Запросов {current.requests}, стоимость ${current.cost_usd:.4f}")


def generate_company(args: argparse.Namespace) -> None:
    """Генерация компании из терминала с выводом этапов."""

    asyncio.run(_generate_company(args))


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m src.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("export-schema", help="Выгрузить JSON Schema карточки в docs/")

    check = commands.add_parser("check-openrouter", help="Проверить ключ и модель OpenRouter")
    check.add_argument("--model", default=None, help="Модель из OPENROUTER_ALLOWED_TEXT_MODELS")
    check.add_argument("--image", action="store_true", help="Сгенерировать тестовое фото")

    generate = commands.add_parser("generate-company", help="Сгенерировать компанию")
    generate.add_argument("--brand", default=None, help="Название бренда")
    generate.add_argument("--scale", choices=["small", "medium"], default=None)
    generate.add_argument("--service-type", default=None, help="Например earnings_analysis")
    generate.add_argument("--model", default=None)
    generate.add_argument("--no-photos", action="store_true", help="Без фото команды")

    args = parser.parse_args()
    {
        "export-schema": export_schema,
        "check-openrouter": check_openrouter,
        "generate-company": generate_company,
    }[args.command](args)


if __name__ == "__main__":
    main()
