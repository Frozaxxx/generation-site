from functools import lru_cache

from src.core.settings import openrouter_config
from src.shared.domain.exceptions import BadRequestError

from .application.protocols import LLMClient
from .domain.budget import OperationBudget
from .domain.exceptions import LLMNotConfiguredError, ModelNotAllowedError
from .infra.openrouter import OpenRouterClient


@lru_cache(maxsize=1)
def get_openrouter_client() -> OpenRouterClient:
    """Один HTTP-клиент на процесс: переиспользует соединения и кеш прайса."""
    return OpenRouterClient(openrouter_config)


def get_llm_client() -> LLMClient:
    return get_openrouter_client()


def ensure_llm_configured() -> None:
    if not openrouter_config.is_configured:
        raise LLMNotConfiguredError()


def resolve_text_model(model: str | None) -> str:
    """Модель из запроса пользователя или модель по умолчанию."""

    model = (model or openrouter_config.text_model).strip()
    if model not in openrouter_config.allowed_text_models:
        raise ModelNotAllowedError(
            f"Модель {model!r} не разрешена",
            details={"allowed": openrouter_config.allowed_text_models},
        )
    return model


def new_budget(limit_usd: float | None = None) -> OperationBudget:
    limit = limit_usd if limit_usd is not None else openrouter_config.operation_budget_usd
    if limit > openrouter_config.operation_budget_usd:
        raise BadRequestError(
            f"Лимит операции не может превышать ${openrouter_config.operation_budget_usd:.2f}"
        )
    return OperationBudget(limit_usd=limit)
