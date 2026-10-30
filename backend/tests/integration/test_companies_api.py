from httpx import AsyncClient

from src.companies.application.services import CompanyService
from src.companies.infra.database.repos.companies import SqlCompanyRepository
from src.core.database import session_factory
from src.shared.application.transaction import Transaction
from tests.support.factories import make_company


async def _create_company() -> str:
    async with session_factory() as session:
        service = CompanyService(SqlCompanyRepository(session), Transaction(session))
        company = await service.save_generated(make_company())
    return str(company.id)


async def test_library_edit_approve_and_export(client: AsyncClient):
    company_id = await _create_company()

    listing = await client.get("/api/v1/companies", params={"search": "kestrel"})
    assert listing.status_code == 200
    assert company_id in {item["id"] for item in listing.json()["items"]}

    company = (await client.get(f"/api/v1/companies/{company_id}")).json()
    assert company["status"] == "draft"
    assert [issue for issue in company["issues"] if issue["severity"] == "error"] == []

    approved = await client.post(f"/api/v1/companies/{company_id}/approve")
    assert approved.json()["status"] == "approved"

    profile = company["profile"]
    profile["brand"]["tagline"] = "Обзоры отчётности для фондов среднего размера"
    edited = await client.put(
        f"/api/v1/companies/{company_id}/profile", json={"profile": profile, "revision": 1}
    )
    assert edited.status_code == 200
    assert edited.json()["revision"] == 2
    assert edited.json()["status"] == "draft"

    stale = await client.put(
        f"/api/v1/companies/{company_id}/profile", json={"profile": profile, "revision": 1}
    )
    assert stale.status_code == 409

    exported = await client.get(f"/api/v1/companies/{company_id}/export")
    assert exported.headers["content-disposition"].startswith("attachment")
    assert exported.json()["profile"]["brand"]["tagline"] == profile["brand"]["tagline"]
    assert "sk-or-test-secret-key" not in exported.text


async def test_invalid_profile_returns_field_errors(client: AsyncClient):
    company_id = await _create_company()
    company = (await client.get(f"/api/v1/companies/{company_id}")).json()
    company["profile"]["contacts"]["phone"] = "не телефон"

    response = await client.put(
        f"/api/v1/companies/{company_id}/profile",
        json={"profile": company["profile"], "revision": company["revision"]},
    )

    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["path"] == "contacts.phone"


async def test_catalog_does_not_leak_key(client: AsyncClient):
    response = await client.get("/api/v1/catalog")

    assert response.status_code == 200
    assert response.json()["countries"] == [
        {"key": "DE", "label": "Германия", "description": None}
    ]
    assert "sk-or-test-secret-key" not in response.text
