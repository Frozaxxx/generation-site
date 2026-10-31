import logging
import re

from src.core.settings import openrouter_config

_KEY_RE = re.compile(r"sk-or-[A-Za-z0-9_\-]{8,}")
REDACTED = "***"


def redact(text: str) -> str:
    """Убирает API-ключи из текста ошибок и логов."""

    secret = openrouter_config.api_key.get_secret_value()
    if secret:
        text = text.replace(secret, REDACTED)
    return _KEY_RE.sub(REDACTED, text)


class SecretRedactingFilter(logging.Filter):
    """Фильтр логов: ключ не попадает в журнал, даже если оказался в сообщении."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        cleaned = redact(message)
        if cleaned != message:
            record.msg, record.args = cleaned, None
        return True
