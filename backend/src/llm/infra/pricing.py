import logging
import time

import httpx

from src.core.settings import OpenRouterConfig

from ..domain.vo import ModelPricing

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 3600
_RETRY_AFTER_FAILURE_SECONDS = 60


def _price(value: object) -> float:
    try:
        return max(float(value), 0.0)  # pyright: ignore[reportArgumentType]
    except TypeError, ValueError:
        return 0.0


class PricingCatalog:
    """Прайс моделей из `GET /models` OpenRouter, кешируется в памяти на час."""

    def __init__(self, config: OpenRouterConfig, http: httpx.AsyncClient) -> None:
        self._config = config
        self._http = http
        self._prices: dict[str, ModelPricing] = {}
        self._loaded_at = 0.0
        self._failed_at: float | None = None

    async def get(self, model: str) -> ModelPricing:
        await self.load()
        if pricing := self._prices.get(model):
            return pricing

        return ModelPricing(
            model=model,
            prompt=self._config.fallback_prompt_price_per_mtok / 1_000_000,
            completion=self._config.fallback_completion_price_per_mtok / 1_000_000,
        )

    def cached(self, model: str) -> ModelPricing | None:
        """Цена из уже загруженного прайса, без сетевого запроса."""
        return self._prices.get(model)

    async def known(self, model: str) -> bool | None:
        """`None` - прайс недоступен, проверить модель нельзя."""

        await self.load()
        if not self._prices:
            return None
        return model in self._prices

    async def load(self) -> None:
        """Загружает прайс, если кеш пуст или устарел. Запрос бесплатный."""

        now = time.monotonic()
        if self._prices and now - self._loaded_at < _CACHE_TTL_SECONDS:
            return
        if self._failed_at is not None and now - self._failed_at < _RETRY_AFTER_FAILURE_SECONDS:
            return

        try:
            response = await self._http.get("/models")
            response.raise_for_status()
            items = response.json().get("data", [])
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("OpenRouter pricing unavailable: %s", type(error).__name__)
            self._failed_at = now
            return

        prices = {}
        for item in items:
            pricing = item.get("pricing") or {}
            prices[item["id"]] = ModelPricing(
                model=item["id"],
                prompt=_price(pricing.get("prompt")),
                completion=_price(pricing.get("completion")),
                context_length=item.get("context_length"),
            )

        self._prices = prices
        self._loaded_at = now
        self._failed_at = None
