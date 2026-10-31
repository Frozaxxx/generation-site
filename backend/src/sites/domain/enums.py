from enum import StrEnum, auto


class SiteLanguage(StrEnum):
    RU = auto()
    DE = auto()


class SiteStatus(StrEnum):
    READY = auto()
    # Собран, но проверки сайта нашли ошибки: показываем, но не выдаём за готовый.
    FAILED_CHECKS = auto()
