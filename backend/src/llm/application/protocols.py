from typing import Protocol

from pydantic import BaseModel

from ..domain.budget import OperationBudget
from ..domain.vo import GeneratedImage


class LLMClient(Protocol):
    async def complete_json[T: BaseModel](
        self,
        *,
        model: str,
        system: str,
        user: str,
        schema: type[T],
        budget: OperationBudget,
        temperature: float = 0.8,
        max_tokens: int = 6000,
    ) -> T:
        """Возвращает ответ модели, проверенный по схеме."""
        ...

    async def generate_image(
        self,
        *,
        model: str,
        prompt: str,
        budget: OperationBudget,
        aspect_ratio: str = "4:5",
    ) -> GeneratedImage:
        """Генерирует одно изображение."""
        ...
