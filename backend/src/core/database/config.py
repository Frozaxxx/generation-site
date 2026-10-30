from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..settings import storage_config


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default=f"sqlite+aiosqlite:///{storage_config.database_path.as_posix()}",
        description="SQLite по умолчанию: проект запускается без внешних сервисов.",
    )
    echo: bool = Field(default=False, description="Для разработки поставить True.")


database_config = DatabaseConfig()
