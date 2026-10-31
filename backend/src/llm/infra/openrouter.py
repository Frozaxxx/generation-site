"""
Клиент OpenRouter: тексты в JSON и фотографии.

- ответы проверяются pydantic-схемой, при ошибке модель получает список ошибок и
  исправляет ответ (это тоже попытка);
- сетевые сбои, 408/429/5xx повторяются с экспоненциальной паузой;
- перед каждым запросом проверяется лимит операции по худшему случаю;
- ключ живёт только в заголовке запроса и вырезается из всех сообщений об ошибках.
"""

from typing import Any

import asyncio
import base64
import binascii
import json
import logging
from collections.abc import Awaitable, Callable

import httpx
from pydantic import BaseModel, ValidationError

from src.core.settings import OpenRouterConfig

from ..domain.budget import OperationBudget
from ..domain.exceptions import (
    InvalidModelResponseError,
    LLMError,
    LLMNotConfiguredError,
)
from ..domain.vo import GeneratedImage, Usage
from .parsing import extract_json
from .pricing import PricingCatalog
from .redaction import redact

logger = logging.getLogger(__name__)

RETRYABLE_STATUSES = frozenset({408, 409, 425, 429, 500, 502, 503, 504})
# Грубая оценка для лимита: ~3 символа кириллицы/латиницы на токен с запасом.
CHARS_PER_TOKEN = 3
MAX_ERROR_DETAILS = 8

Sleep = Callable[[float], Awaitable[None]]


class _RetryableError(Exception):
    """Внутренний сигнал: попытку можно повторить."""

    def __init__(self, reason: str, *, retry_after: float | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.retry_after = retry_after


def _validation_feedback(error: ValidationError) -> str:
    """Ошибки схемы в виде, понятном модели: где, что не так и что сделать."""

    lines = []
    for item in error.errors(include_url=False)[:MAX_ERROR_DETAILS]:
        path = ".".join(str(part) for part in item["loc"]) or "<root>"
        ctx = item.get("ctx") or {}
        value = item.get("input")

        if item["type"] == "string_too_long" and isinstance(value, str):
            limit = ctx.get("max_length")
            message = (
                f"сейчас {len(value)} символов, нужно не больше {limit}. "
                f"Перепиши короче, примерно до {int(limit * 0.8)} символов"
            )
        elif item["type"] == "string_too_short" and isinstance(value, str):
            message = f"сейчас {len(value)} символов, нужно не меньше {ctx.get('min_length')}"
        elif item["type"] in {"too_long", "too_short"} and isinstance(value, list):
            message = f"{item['msg']} (сейчас {len(value)})"
        else:
            message = item["msg"]
        lines.append(f"- {path}: {message}")

    return "\n".join(lines)


def _usage_from(payload: dict[str, Any]) -> tuple[int, int, float | None]:
    usage = payload.get("usage") or {}
    cost = usage.get("cost")
    return (
        int(usage.get("prompt_tokens") or 0),
        int(usage.get("completion_tokens") or 0),
        float(cost) if cost is not None else None,
    )


class OpenRouterClient:
    def __init__(
        self,
        config: OpenRouterConfig,
        *,
        http: httpx.AsyncClient | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._config = config
        self._http = http or httpx.AsyncClient(
            base_url=config.base_url,
            timeout=httpx.Timeout(config.request_timeout, connect=10.0),
        )
        self._sleep = sleep
        self.pricing = PricingCatalog(config, self._http)

    async def aclose(self) -> None:
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Тексты
    # ------------------------------------------------------------------

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
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        use_schema = True
        last_reason = ""

        for attempt in range(self._config.max_retries + 1):
            body: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if use_schema:
                body["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "strict": False,
                        "schema": schema.model_json_schema(),
                    },
                }
            else:
                body["response_format"] = {"type": "json_object"}

            prompt_chars = sum(len(message["content"]) for message in messages)
            pricing = await self.pricing.get(model)
            budget.ensure_can_spend(pricing.cost(prompt_chars // CHARS_PER_TOKEN, max_tokens))

            try:
                payload = await self._post("/chat/completions", body, model, budget)
            except _RetryableError as error:
                last_reason = error.reason
                await self._backoff(attempt, error.retry_after, model, error.reason)
                continue
            except LLMError as error:
                # Не все провайдеры понимают json_schema: повторяем без неё.
                if use_schema and error.details.get("status") == httpx.codes.BAD_REQUEST:
                    use_schema = False
                    last_reason = "response_format json_schema не поддерживается"
                    continue
                raise

            content = self._message_content(payload)
            try:
                return schema.model_validate(extract_json(content))
            except ValueError as error:
                # ValidationError - подкласс ValueError, разбираем оба случая.
                feedback = (
                    _validation_feedback(error)
                    if isinstance(error, ValidationError)
                    else str(error)
                )
                last_reason = f"ответ не прошёл проверку схемы:\n{feedback}"
                logger.warning(
                    "Invalid model response",
                    extra={"model": model, "attempt": attempt + 1, "errors": feedback},
                )
                messages = [
                    *messages[:2],
                    {"role": "assistant", "content": content[:20_000]},
                    {
                        "role": "user",
                        "content": (
                            "Ответ не прошёл проверку. Исправь ошибки и верни полный JSON "
                            f"целиком, без пояснений:\n{feedback}"
                        ),
                    },
                ]

        raise InvalidModelResponseError(
            f"Модель {model} не дала корректный ответ за {self._config.max_retries + 1} попыток",
            details={"reason": redact(last_reason)[:2000]},
        )

    @staticmethod
    def _message_content(payload: dict[str, Any]) -> str:
        try:
            content = payload["choices"][0]["message"]["content"]
        except KeyError, IndexError, TypeError:
            content = None

        if isinstance(content, list):  # часть провайдеров отдаёт список блоков
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))

        if not isinstance(content, str) or not content.strip():
            # Пустой ответ - тоже повод для повтора через проверку схемы.
            return ""
        return content

    # ------------------------------------------------------------------
    # Изображения
    # ------------------------------------------------------------------

    async def generate_image(
        self,
        *,
        model: str,
        prompt: str,
        budget: OperationBudget,
        aspect_ratio: str = "4:5",
    ) -> GeneratedImage:
        use_images_api = True
        last_reason = ""

        for attempt in range(self._config.max_retries + 1):
            budget.ensure_can_spend(self._config.image_cost_estimate_usd)
            try:
                if use_images_api:
                    payload = await self._post(
                        "/images",
                        {"model": model, "prompt": prompt, "n": 1, "aspect_ratio": aspect_ratio},
                        model,
                        budget,
                    )
                    image = self._image_from_images_api(payload)
                else:
                    payload = await self._post(
                        "/chat/completions",
                        {
                            "model": model,
                            "messages": [{"role": "user", "content": prompt}],
                            "modalities": ["image", "text"],
                            "image_config": {"aspect_ratio": aspect_ratio},
                        },
                        model,
                        budget,
                    )
                    image = self._image_from_chat(payload)
            except _RetryableError as error:
                last_reason = error.reason
                await self._backoff(attempt, error.retry_after, model, error.reason)
                continue
            except LLMError as error:
                # Старые аккаунты/модели без Images API - пробуем через chat completions.
                if use_images_api and error.details.get("status") in {404, 405}:
                    use_images_api = False
                    continue
                raise

            if image is not None:
                return image
            last_reason = "в ответе нет изображения"

        raise InvalidModelResponseError(
            f"Модель {model} не вернула изображение",
            details={"reason": last_reason},
        )

    @staticmethod
    def _decode(data: str, media_type: str | None) -> GeneratedImage | None:
        if data.startswith("data:"):
            header, _, data = data.partition(",")
            media_type = header.removeprefix("data:").split(";")[0] or media_type
        try:
            content = base64.b64decode(data, validate=True)
        except ValueError, binascii.Error:
            return None
        if not content:
            return None
        return GeneratedImage(content=content, media_type=media_type or "image/png")

    def _image_from_images_api(self, payload: dict[str, Any]) -> GeneratedImage | None:
        for item in payload.get("data") or []:
            if data := item.get("b64_json"):
                return self._decode(data, item.get("media_type"))
        return None

    def _image_from_chat(self, payload: dict[str, Any]) -> GeneratedImage | None:
        try:
            images = payload["choices"][0]["message"].get("images") or []
        except KeyError, IndexError, TypeError, AttributeError:
            return None
        for image in images:
            url = (image.get("image_url") or {}).get("url", "")
            if url:
                return self._decode(url, None)
        return None

    # ------------------------------------------------------------------
    # Транспорт
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        secret = self._config.api_key.get_secret_value()
        if not secret:
            raise LLMNotConfiguredError()
        return {
            "Authorization": f"Bearer {secret}",
            "X-Title": self._config.app_title,
        }

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        model: str,
        budget: OperationBudget,
    ) -> dict[str, Any]:
        try:
            response = await self._http.post(path, json=body, headers=self._headers())
        except httpx.TimeoutException:
            raise _RetryableError("таймаут запроса") from None
        except httpx.TransportError as error:
            raise _RetryableError(f"сетевая ошибка {type(error).__name__}") from None

        payload = self._json(response)
        self._charge(payload, body, model, budget)

        if response.status_code in RETRYABLE_STATUSES:
            retry_after = response.headers.get("retry-after")
            raise _RetryableError(
                f"HTTP {response.status_code}: {self._error_message(payload)}",
                retry_after=float(retry_after) if retry_after and retry_after.isdigit() else None,
            )

        if response.status_code >= httpx.codes.BAD_REQUEST:
            raise LLMError(
                f"OpenRouter вернул HTTP {response.status_code}: {self._error_message(payload)}",
                details={"status": response.status_code, "model": model},
            )

        # OpenRouter может вернуть 200 с ошибкой провайдера внутри.
        if "error" in payload and not payload.get("choices") and not payload.get("data"):
            raise _RetryableError(f"ошибка провайдера: {self._error_message(payload)}")

        return payload

    @staticmethod
    def _json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except json.JSONDecodeError, ValueError:
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _error_message(payload: dict[str, Any]) -> str:
        error = payload.get("error")
        message = error.get("message") if isinstance(error, dict) else error
        return redact(str(message or "без описания"))[:300]

    def _charge(
        self,
        payload: dict[str, Any],
        body: dict[str, Any],
        model: str,
        budget: OperationBudget,
    ) -> None:
        """Учитывает стоимость запроса, даже если ответ потом окажется негодным."""

        input_tokens, output_tokens, cost = _usage_from(payload)
        if not (input_tokens or output_tokens or cost):
            return

        if cost is None:
            # Стоимости нет в ответе: считаем по прайсу, если он уже загружен.
            pricing = self.pricing.cached(model)
            cost = pricing.cost(input_tokens, output_tokens) if pricing else 0.0
            reported = False
        else:
            reported = True

        budget.add(
            Usage(
                model=body.get("model", model),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                cost_reported=reported,
            )
        )

    async def _backoff(
        self,
        attempt: int,
        retry_after: float | None,
        model: str,
        reason: str,
    ) -> None:
        if attempt >= self._config.max_retries:
            raise LLMError(
                f"Модель {model} недоступна после {attempt + 1} попыток: {redact(reason)}",
                details={"model": model},
            )
        delay = retry_after if retry_after is not None else min(2**attempt, 20)
        logger.warning(
            "OpenRouter request retry",
            extra={"model": model, "attempt": attempt + 1, "reason": redact(reason)},
        )
        await self._sleep(delay)
