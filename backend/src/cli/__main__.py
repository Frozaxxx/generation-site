"""
Служебные команды: `python -m src.cli <команда>`.
"""

import argparse
import json
import sys

from src.companies.domain.serialization import profile_json_schema
from src.core.settings import DOCS_DIR

SCHEMA_FILE = DOCS_DIR / "company.schema.json"


def export_schema() -> None:
    """Сохраняет JSON Schema карточки компании в docs/."""

    SCHEMA_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_FILE.write_text(
        json.dumps(profile_json_schema(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    sys.stdout.write(f"Схема сохранена: {SCHEMA_FILE}\n")


COMMANDS = {"export-schema": export_schema}


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m src.cli")
    parser.add_argument("command", choices=sorted(COMMANDS))
    args = parser.parse_args()
    COMMANDS[args.command]()


if __name__ == "__main__":
    main()
