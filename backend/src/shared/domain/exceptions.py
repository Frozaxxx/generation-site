from fastapi import status


class DomainError(Exception):
    """Базовая ошибка приложения - от него наследуются все доменные исключения"""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_SERVER_ERROR"
    public_message: str = "Внутренняя ошибка сервера"

    def __init__(
        self,
        message: str | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
        details: dict | list | None = None,
    ):
        self.message = message or self.public_message
        self.status_code = status_code or self.status_code
        self.error_code = error_code or self.error_code
        self.details = details or {}
        super().__init__(self.message)


class BadRequestError(DomainError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BAD_REQUEST"
    public_message = "Некорректный запрос"


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "RESOURCE_NOT_FOUND"
    public_message = "Ресурс не найден"


class InvariantViolationError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "INVARIANT_VIOLATION"
    public_message = "Нарушены условия существования объекта"


class InvalidStateError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "INVALID_STATE"
    public_message = "Невалидное состояние объекта"
