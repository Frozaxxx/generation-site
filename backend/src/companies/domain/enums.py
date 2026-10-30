from enum import StrEnum, auto


class CompanyScale(StrEnum):
    """Масштаб компании."""

    SMALL = auto()
    MEDIUM = auto()


class CompanyStatus(StrEnum):
    """Жизненный цикл карточки: черновик можно править, утверждённая идёт в сайт."""

    DRAFT = auto()
    APPROVED = auto()


class Gender(StrEnum):
    FEMALE = auto()
    MALE = auto()


class TeamRole(StrEnum):
    """Место человека в структуре компании."""

    CEO = auto()
    DEPARTMENT_HEAD = auto()
    SPECIALIST = auto()


class IssueSeverity(StrEnum):
    """Ошибка блокирует утверждение карточки, предупреждение - нет."""

    ERROR = auto()
    WARNING = auto()
