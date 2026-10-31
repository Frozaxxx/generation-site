from fastapi import status

from src.shared.domain.exceptions import BadRequestError, DomainError


class LLMError(DomainError):
    """Модель или OpenRouter не смогли выполнить запрос."""

    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "LLM_ERROR"
    public_message = "Ошибка при обращении к модели"


class LLMNotConfiguredError(DomainError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "LLM_NOT_CONFIGURED"
    public_message = "Не задан OPENROUTER_API_KEY в backend/.env"


class InvalidModelResponseError(LLMError):
    error_code = "LLM_INVALID_RESPONSE"
    public_message = "Модель вернула некорректный ответ"


class BudgetExceededError(DomainError):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    error_code = "BUDGET_EXCEEDED"
    public_message = "Превышен лимит расходов на операцию"


class ModelNotAllowedError(BadRequestError):
    error_code = "MODEL_NOT_ALLOWED"
    public_message = "Модель не входит в список разрешённых"
