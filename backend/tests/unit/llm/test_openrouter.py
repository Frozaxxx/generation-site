import base64
import json
import logging

import httpx
import pytest
from pydantic import BaseModel, Field

from src.core.settings import OpenRouterConfig
from src.llm.domain.budget import OperationBudget
from src.llm.domain.exceptions import (
    BudgetExceededError,
    InvalidModelResponseError,
    LLMError,
    LLMNotConfiguredError,
)
from src.llm.infra.openrouter import OpenRouterClient
from src.llm.infra.redaction import SecretRedactingFilter, redact

SECRET = "sk-or-test-secret-key"  # noqa: S105
MODEL = "google/gemini-2.5-flash"
MODELS_PAYLOAD = {
    "data": [
        {"id": MODEL, "pricing": {"prompt": "0.0000003", "completion": "0.0000025"}},
    ]
}


class Answer(BaseModel):
    city: str
    employees: int


def chat(content: str, cost: float = 0.001) -> dict:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "cost": cost},
    }


class FakeOpenRouter:
    """Подменяет HTTP: отдаёт заранее заданные ответы и запоминает запросы."""

    def __init__(self, responses: list[httpx.Response | Exception]) -> None:
        self.responses = responses
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json=MODELS_PAYLOAD)
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def bodies(self) -> list[dict]:
        return [json.loads(request.content) for request in self.requests]


def make_client(fake: FakeOpenRouter, **config) -> OpenRouterClient:
    settings = OpenRouterConfig(api_key=SECRET, max_retries=2, **config)  # pyright: ignore[reportArgumentType]
    http = httpx.AsyncClient(
        base_url="https://openrouter.test/api/v1", transport=httpx.MockTransport(fake)
    )

    async def no_sleep(_delay: float) -> None:
        return None

    return OpenRouterClient(settings, http=http, sleep=no_sleep)


async def ask(client: OpenRouterClient, budget: OperationBudget | None = None) -> Answer:
    return await client.complete_json(
        model=MODEL,
        system="system",
        user="user",
        schema=Answer,
        budget=budget or OperationBudget(limit_usd=1.0),
        max_tokens=1000,
    )


async def test_valid_json_and_cost_accounting():
    fake = FakeOpenRouter([httpx.Response(200, json=chat('{"city": "Köln", "employees": 12}'))])
    budget = OperationBudget(limit_usd=1.0)

    answer = await ask(make_client(fake), budget)

    assert answer == Answer(city="Köln", employees=12)
    assert budget.requests == 1
    assert budget.spent_usd == pytest.approx(0.001)
    assert fake.requests[0].headers["authorization"] == f"Bearer {SECRET}"
    assert fake.bodies()[0]["response_format"]["type"] == "json_schema"


async def test_markdown_fence_is_accepted():
    content = '```json\n{"city": "Hamburg", "employees": 40}\n```'
    fake = FakeOpenRouter([httpx.Response(200, json=chat(content))])

    assert (await ask(make_client(fake))).city == "Hamburg"


async def test_invalid_answer_is_repaired_with_feedback():
    fake = FakeOpenRouter(
        [
            httpx.Response(200, json=chat('{"city": "Berlin", "employees": "много"}')),
            httpx.Response(200, json=chat('{"city": "Berlin", "employees": 25}')),
        ]
    )
    budget = OperationBudget(limit_usd=1.0)

    answer = await ask(make_client(fake), budget)

    assert answer.employees == 25
    repair_messages = fake.bodies()[1]["messages"]
    assert repair_messages[-1]["role"] == "user"
    assert "employees" in repair_messages[-1]["content"]
    # Негодный ответ тоже стоит денег и учитывается.
    assert budget.requests == 2


async def test_repair_feedback_explains_length():
    long_city = "Б" * 50

    class Short(BaseModel):
        city: str = Field(max_length=20)

    fake = FakeOpenRouter(
        [
            httpx.Response(200, json=chat(json.dumps({"city": long_city}))),
            httpx.Response(200, json=chat('{"city": "Berlin"}')),
        ]
    )

    await make_client(fake).complete_json(
        model=MODEL, system="s", user="u", schema=Short, budget=OperationBudget(limit_usd=1)
    )

    feedback = fake.bodies()[1]["messages"][-1]["content"]
    assert "сейчас 50 символов, нужно не больше 20" in feedback


async def test_retries_are_limited():
    fake = FakeOpenRouter([httpx.Response(200, json=chat("не json")) for _ in range(3)])

    with pytest.raises(InvalidModelResponseError):
        await ask(make_client(fake))

    assert len(fake.requests) == 3


async def test_server_errors_are_retried():
    fake = FakeOpenRouter(
        [
            httpx.Response(503, json={"error": {"message": "overloaded"}}),
            httpx.ConnectTimeout("timeout"),
            httpx.Response(200, json=chat('{"city": "München", "employees": 9}')),
        ]
    )

    assert (await ask(make_client(fake))).city == "München"
    assert len(fake.requests) == 3


async def test_retryable_errors_exhausted():
    fake = FakeOpenRouter([httpx.Response(429, json={"error": "rate"}) for _ in range(3)])

    with pytest.raises(LLMError, match="недоступна"):
        await ask(make_client(fake))


async def test_auth_error_is_not_retried_and_hides_key():
    fake = FakeOpenRouter(
        [httpx.Response(401, json={"error": {"message": f"Invalid key {SECRET}"}})]
    )

    with pytest.raises(LLMError) as error:
        await ask(make_client(fake))

    assert len(fake.requests) == 1
    assert SECRET not in str(error.value)
    assert SECRET not in json.dumps(error.value.details)


async def test_falls_back_when_json_schema_unsupported():
    fake = FakeOpenRouter(
        [
            httpx.Response(400, json={"error": {"message": "response_format not supported"}}),
            httpx.Response(200, json=chat('{"city": "Berlin", "employees": 5}')),
        ]
    )

    await ask(make_client(fake))

    assert fake.bodies()[1]["response_format"] == {"type": "json_object"}


async def test_budget_blocks_request_before_sending():
    fake = FakeOpenRouter([])
    budget = OperationBudget(limit_usd=0.001)

    with pytest.raises(BudgetExceededError):
        await ask(make_client(fake), budget)

    assert fake.requests == []


async def test_budget_stops_after_spending():
    fake = FakeOpenRouter([httpx.Response(200, json=chat("не json", cost=0.009))])
    budget = OperationBudget(limit_usd=0.01)

    with pytest.raises(BudgetExceededError):
        await ask(make_client(fake), budget)

    assert len(fake.requests) == 1
    assert budget.spent_usd == pytest.approx(0.009)


async def test_missing_key():
    client = make_client(FakeOpenRouter([]))
    client._config = OpenRouterConfig(api_key="")  # pyright: ignore[reportArgumentType]

    with pytest.raises(LLMNotConfiguredError):
        await ask(client)


async def test_image_from_images_api():
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
    fake = FakeOpenRouter(
        [
            httpx.Response(
                200,
                json={
                    "data": [
                        {"b64_json": base64.b64encode(png).decode(), "media_type": "image/png"}
                    ],
                    "usage": {"cost": 0.04},
                },
            )
        ]
    )
    budget = OperationBudget(limit_usd=1.0)

    image = await make_client(fake).generate_image(model="img", prompt="portrait", budget=budget)

    assert image.content == png
    assert image.extension == "png"
    assert budget.spent_usd == pytest.approx(0.04)
    assert fake.requests[0].url.path.endswith("/images")


async def test_image_falls_back_to_chat_modalities():
    data_url = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xffjpeg").decode()
    fake = FakeOpenRouter(
        [
            httpx.Response(404, json={"error": "not found"}),
            httpx.Response(
                200,
                json={"choices": [{"message": {"images": [{"image_url": {"url": data_url}}]}}]},
            ),
        ]
    )

    image = await make_client(fake).generate_image(
        model="img", prompt="portrait", budget=OperationBudget(limit_usd=1.0)
    )

    assert image.media_type == "image/jpeg"
    assert fake.bodies()[1]["modalities"] == ["image", "text"]


def test_redaction_in_text_and_logs(caplog: pytest.LogCaptureFixture):
    assert SECRET not in redact(f"Bearer {SECRET}")
    assert "sk-or-" not in redact("ключ sk-or-v1-abcdef0123456789")

    logger = logging.getLogger("test.redaction")
    logger.addFilter(SecretRedactingFilter())
    with caplog.at_level(logging.INFO, logger="test.redaction"):
        logger.info("Authorization: Bearer %s", SECRET)

    assert SECRET not in caplog.text
