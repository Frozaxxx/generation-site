import contextlib
import importlib
from collections.abc import Sequence

from .base import Base
from .config import database_config
from .connection import engine, get_db, session_factory


def import_all_models(modules: Sequence[str]) -> None:
    """Импортирует ORM модели модулей из `src.{module}.infra.database.models`,
    чтобы они попали в метаданные для миграций.
    """

    for module in modules:
        with contextlib.suppress(ModuleNotFoundError):
            importlib.import_module(f"src.{module}.infra.database.models")


__all__ = [
    "Base",
    "database_config",
    "engine",
    "get_db",
    "import_all_models",
    "session_factory",
]
