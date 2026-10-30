from alembic import command
from alembic.config import Config

from .database import database_config
from .settings import BASE_DIR


def upgrade_database() -> None:
    """Применяет миграции до последней версии."""

    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", database_config.url)
    command.upgrade(config, "head")
