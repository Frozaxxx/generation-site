from collections.abc import Iterator

import pytest
from httpx import AsyncClient

from main import app
from src.companies.application.generation.pipeline import CompanyGenerator
from src.companies.application.generation.service import CompanyAIService, CompanyGenerationService
from src.companies.dependencies.base import CompanyRepoDep
from src.companies.dependencies.generation import get_ai_service, get_generation_service
from src.core.database import session_factory
from src.jobs.dependencies import JobRunnerDep, job_runner
from src.shared.dependencies.database import TransactionDep
from tests.support.fake_llm import FakeLLM


@pytest.fixture
def fake_llm() -> Iterator[FakeLLM]:
    llm = FakeLLM()

    def generation(runner: JobRunnerDep) -> CompanyGenerationService:
        return CompanyGenerationService(runner, CompanyGenerator(llm, session_factory))

    def ai(repo: CompanyRepoDep, transaction: TransactionDep) -> CompanyAIService:
        return CompanyAIService(repo, transaction, llm)

    app.dependency_overrides[get_generation_service] = generation
    app.dependency_overrides[get_ai_service] = ai
    yield llm
    app.dependency_overrides.clear()


async def _generate(client: AsyncClient, **body) -> dict:
    response = await client.post("/api/v1/companies/generate", json=body)
    assert response.status_code == 202, response.text
    job_id = response.json()["id"]
    await job_runner.wait_all()

    job = (await client.get(f"/api/v1/jobs/{job_id}")).json()
    assert job["status"] == "succeeded", job
    return job


async def test_generate_company_end_to_end(client: AsyncClient, fake_llm: FakeLLM):
    job = await _generate(client, scale="small", country="DE")

    assert job["stages"] == ["concept", "texts", "review", "photos", "save"]
    assert job["cost_usd"] > 0
    assert fake_llm.calls[0] == "ConceptDraft"
    assert set(fake_llm.calls[1:3]) == {"ProductDraft", "TeamDraft"}
    assert fake_llm.calls[3] == "ReviewDraft"
    assert fake_llm.calls.count("image") == 5

    company = (await client.get(f"/api/v1/companies/{job['result_id']}")).json()
    profile = company["profile"]
    assert [issue for issue in company["issues"] if issue["severity"] == "error"] == []
    assert company["params"]["scale"] == "small"
    assert len(profile["team"]) == 5
    assert all(person["photo"] for person in profile["team"])
    assert company["generation"]["cost_usd"] == job["cost_usd"]

    photo = profile["team"][0]["photo"]["file"]
    image = await client.get(f"/media/companies/{company['id']}/{photo}")
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"


async def test_generate_without_photos_and_with_brand(client: AsyncClient, fake_llm: FakeLLM):
    job = await _generate(client, brand_name="Nordlicht Research", with_photos=False)

    assert "photos" not in job["stages"]
    company = (await client.get(f"/api/v1/companies/{job['result_id']}")).json()
    assert company["profile"]["brand"]["legal_name"].startswith("Nordlicht Research ")
    assert company["profile"]["brand"]["domain"].startswith("nordlicht-research.")
    assert "image" not in fake_llm.calls


async def test_regenerate_photo_keeps_revision(client: AsyncClient, fake_llm: FakeLLM):
    job = await _generate(client, with_photos=False)
    company_id = job["result_id"]
    company = (await client.get(f"/api/v1/companies/{company_id}")).json()
    person_id = company["profile"]["team"][0]["id"]

    response = await client.post(f"/api/v1/companies/{company_id}/team/{person_id}/photo", json={})

    assert response.status_code == 200
    updated = response.json()
    assert updated["profile"]["team"][0]["photo"]["file"] == f"team/{person_id}.jpg"
    assert updated["revision"] == company["revision"]


async def test_model_must_be_allowed(client: AsyncClient, fake_llm: FakeLLM):
    response = await client.post("/api/v1/companies/generate", json={"model": "some/unknown"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MODEL_NOT_ALLOWED"


async def test_review_errors_trigger_one_revision(client: AsyncClient, fake_llm: FakeLLM):
    issue = {"path": "product.summary", "severity": "error", "message": "Обещает рекомендации"}
    fake_llm.review_issues = [[issue], [issue]]

    job = await _generate(client, with_photos=False)

    assert fake_llm.calls.count("RevisionDraft") == 1
    assert fake_llm.calls.count("ReviewDraft") == 2
    company = (await client.get(f"/api/v1/companies/{job['result_id']}")).json()
    assert company["profile"]["brand"]["tagline"] == "Исправленный слоган без обещаний"
    review = [i for i in company["issues"] if i["code"].startswith("review_")]
    assert review
    assert all(i["severity"] == "warning" for i in review)
