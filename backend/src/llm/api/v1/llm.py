from fastapi import APIRouter
from pydantic import BaseModel

from src.core.settings import openrouter_config

from ...dependencies import get_openrouter_client

router = APIRouter(prefix="/llm", tags=["Модели"])


class ModelOption(BaseModel):
    id: str
    prompt_per_mtok: float | None
    completion_per_mtok: float | None


class LLMStatus(BaseModel):
    """Настройки генерации без секретов: ключ сообщается только как «задан / не задан»."""

    configured: bool
    default_text_model: str
    image_model: str
    operation_budget_usd: float
    max_retries: int
    models: list[ModelOption]


@router.get("/status", response_model=LLMStatus)
async def get_status() -> LLMStatus:
    pricing = get_openrouter_client().pricing
    await pricing.load()
    models = []
    for model in openrouter_config.allowed_text_models:
        price = pricing.cached(model)
        models.append(
            ModelOption(
                id=model,
                prompt_per_mtok=round(price.prompt * 1_000_000, 4) if price else None,
                completion_per_mtok=round(price.completion * 1_000_000, 4) if price else None,
            )
        )

    return LLMStatus(
        configured=openrouter_config.is_configured,
        default_text_model=openrouter_config.text_model,
        image_model=openrouter_config.image_model,
        operation_budget_usd=openrouter_config.operation_budget_usd,
        max_retries=openrouter_config.max_retries,
        models=models,
    )
