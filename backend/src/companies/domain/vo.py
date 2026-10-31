from dataclasses import dataclass, field

from src.shared.domain.vo import ValueObject

from .enums import CompanyScale


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationParams(ValueObject):
    """Итоговые параметры генерации.

    Пользователь может задать значение или оставить выбор каталогу, в
    `randomized` запоминаем, какие поля были выбраны случайно.
    """

    brand_name: str | None = None
    country: str
    direction: str
    service_type: str
    scale: CompanyScale
    model: str
    randomized: tuple[str, ...] = field(default_factory=tuple)
    # Свои варианты, если пользователь описал направление или сервис текстом.
    custom_direction: str | None = None
    custom_service: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationInfo(ValueObject):
    """Сведения о том, как и за сколько была получена карточка."""

    model: str
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    requests: int = 0
    duration_seconds: float = 0.0
    concept: dict[str, str] = field(default_factory=dict)
    # Смысловая проверка моделью и ревизия карточки, к которой она относится.
    review: list[dict[str, str]] = field(default_factory=list)
    review_revision: int | None = None
    warnings: list[str] = field(default_factory=list)
