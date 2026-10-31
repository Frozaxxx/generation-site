from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

TIMEZONE = "Europe/Berlin"
timezone = ZoneInfo(TIMEZONE)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

INSTALLED_MODULES: tuple[str, ...] = (  # Добавь сюда модуль который готов к использованию
    "companies",
    "jobs",
    "llm",
    "sites",
)

# Рабочие данные приложения: база, фото команды, собранные сайты.
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR.parent / "docs"


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    name: str = Field(default="Generation Site", description="Название приложения.")
    host: str = Field(default="127.0.0.1", description="В Docker - 0.0.0.0.")
    port: int = 8000
    version: str = Field(default="0.1.0", description="Актуальная версия приложения.")

    cors_origins: list[str] = ["http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]


class OpenRouterConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENROUTER_")

    # SecretStr не даёт ключу попасть в repr, логи и ответы API.
    api_key: SecretStr = SecretStr("")
    base_url: str = "https://openrouter.ai/api/v1"

    text_model: str = Field(
        default="google/gemini-2.5-flash",
        description="Модель по умолчанию для текстов.",
    )
    image_model: str = Field(
        default="google/gemini-2.5-flash-image",
        description="Модель для фотографий команды.",
    )
    allowed_text_models: list[str] = [
        "google/gemini-2.5-flash",
        "google/gemini-2.5-pro",
        "openai/gpt-4.1-mini",
        "anthropic/claude-sonnet-4.5",
    ]

    image_cost_estimate_usd: float = Field(
        default=0.05,
        ge=0,
        description="Оценка стоимости одного фото, если прайс модели недоступен.",
    )
    fallback_prompt_price_per_mtok: float = Field(
        default=3.0,
        description="Цена за 1M входных токенов, если модели нет в прайсе OpenRouter.",
    )
    fallback_completion_price_per_mtok: float = Field(default=15.0)
    app_title: str = Field(default="Generation Site", description="X-Title для OpenRouter.")

    max_retries: int = Field(default=3, ge=0, le=5, description="Повторы на один запрос.")
    request_timeout: float = Field(default=120.0, gt=0)
    operation_budget_usd: float = Field(
        default=1.0,
        gt=0,
        description="Лимит расходов на одну операцию (генерация компании или сайта).",
    )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key.get_secret_value())


class StorageConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STORAGE_")

    data_dir: Path = DATA_DIR

    @property
    def database_path(self) -> Path:
        return self.data_dir / "app.sqlite3"

    @property
    def media_dir(self) -> Path:
        return self.data_dir / "media"

    @property
    def sites_dir(self) -> Path:
        return self.data_dir / "sites"


app_config = AppConfig()
openrouter_config = OpenRouterConfig()
storage_config = StorageConfig()
