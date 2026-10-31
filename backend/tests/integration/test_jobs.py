import asyncio

from httpx import AsyncClient

from src.core.database import session_factory
from src.jobs.application.runner import JobContext, JobRunner
from src.jobs.domain.enums import JobKind
from src.llm.domain.budget import OperationBudget
from src.llm.domain.exceptions import BudgetExceededError
from src.llm.domain.vo import Usage


async def test_job_runs_stages_and_reports_cost(client: AsyncClient):
    runner = JobRunner(session_factory)

    async def handler(context: JobContext) -> None:
        await context.stage("concept", "придумываю концепцию")
        context.budget.add(Usage(model="m", cost_usd=0.02))
        await context.stage("team")
        await context.note("фото 2 из 5")

    job = await runner.submit(
        kind=JobKind.COMPANY,
        stages=["concept", "team"],
        params={"brand_name": None},
        handler=handler,
        budget=OperationBudget(limit_usd=0.5),
    )
    await runner.wait_all()

    data = (await client.get(f"/api/v1/jobs/{job.id}")).json()
    assert data["status"] == "succeeded"
    assert data["progress"] == 1.0
    assert data["cost_usd"] == 0.02
    assert data["requests"] == 1


async def test_failed_job_keeps_domain_error(client: AsyncClient):
    runner = JobRunner(session_factory)

    async def handler(context: JobContext) -> None:
        await context.stage("concept")
        context.budget.ensure_can_spend(10)

    job = await runner.submit(
        kind=JobKind.SITE,
        stages=["concept"],
        params={},
        handler=handler,
        budget=OperationBudget(limit_usd=0.5),
    )
    await runner.wait_all()

    data = (await client.get(f"/api/v1/jobs/{job.id}")).json()
    assert data["status"] == "failed"
    assert data["error"]["code"] == BudgetExceededError.error_code
    assert data["stage"] == "concept"


async def test_unexpected_error_is_hidden(client: AsyncClient):
    runner = JobRunner(session_factory)

    async def handler(_context: JobContext) -> None:
        raise RuntimeError("sk-or-test-secret-key leaked in traceback")

    job = await runner.submit(
        kind=JobKind.SITE,
        stages=["x"],
        params={},
        handler=handler,
        budget=OperationBudget(limit_usd=0.5),
    )
    await runner.wait_all()

    response = await client.get(f"/api/v1/jobs/{job.id}")
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "sk-or-" not in response.text


async def test_recover_marks_unfinished_jobs(client: AsyncClient):
    runner = JobRunner(session_factory)
    job = await runner.submit(
        kind=JobKind.SITE,
        stages=["x"],
        params={},
        handler=lambda _context: _never(),
        budget=OperationBudget(limit_usd=0.5),
    )
    await runner.shutdown()

    data = (await client.get(f"/api/v1/jobs/{job.id}")).json()
    assert data["status"] == "failed"
    assert data["error"]["code"] in {"CANCELLED", "INTERRUPTED"}


async def _never() -> None:
    await asyncio.Event().wait()


async def test_llm_status_has_no_secret(client: AsyncClient):
    response = await client.get("/api/v1/llm/status")

    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert "sk-or-" not in response.text
