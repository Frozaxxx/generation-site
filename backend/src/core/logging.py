import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def configure_logging(log_level: str = "INFO") -> logging.Logger:
    """Настройка логирования в формате JSON."""

    level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(lineno)d",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
        timestamp=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for old_handler in root_logger.handlers[:]:
        root_logger.removeHandler(old_handler)

    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # httpx пишет полный URL запроса в INFO, держим его тише.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger
