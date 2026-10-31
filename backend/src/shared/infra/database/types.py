from datetime import datetime

from src.core.settings import timezone


def aware(value: datetime | None) -> datetime | None:
    """SQLite теряет часовой пояс, возвращаем его при чтении."""

    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone)
