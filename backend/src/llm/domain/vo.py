from dataclasses import dataclass

from src.shared.domain.vo import ValueObject


@dataclass(frozen=True, slots=True, kw_only=True)
class Usage(ValueObject):
    """Токены и стоимость одного запроса к модели."""

    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    # Стоимость пришла от OpenRouter, а не посчитана по прайсу.
    cost_reported: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelPricing(ValueObject):
    """Цены модели в USD за один токен."""

    model: str
    prompt: float
    completion: float
    context_length: int | None = None

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return input_tokens * self.prompt + output_tokens * self.completion


@dataclass(frozen=True, slots=True, kw_only=True)
class GeneratedImage(ValueObject):
    content: bytes
    media_type: str

    @property
    def extension(self) -> str:
        return {"image/jpeg": "jpg", "image/webp": "webp"}.get(self.media_type, "png")
