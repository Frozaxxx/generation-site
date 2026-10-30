from datetime import datetime

from ...core.settings import timezone


def current_datetime() -> datetime:
    """Текущее время в указанном часовом поясе."""

    return datetime.now(timezone)
