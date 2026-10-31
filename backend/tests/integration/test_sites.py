import io
import zipfile

import pytest
from httpx import AsyncClient

from main import app
from src.companies.dependencies import CompanyRepoDep
from src.core.database import session_factory
from src.jobs.dependencies import JobRunnerDep, job_runner
from src.sites.application.pipeline import SiteBuilder
from src.sites.application.service import SiteService
from src.sites.dependencies import SiteRepoDep, get_site_service
from tests.integration.test_generation import _generate, fake_llm
from tests.support.fake_llm import FakeLLM


@pytest.fixture
def site_llm(fake_llm: FakeLLM) -> FakeLLM:  # noqa: F811
    def sites(companies: CompanyRepoDep, repo: SiteRepoDep, runner: JobRunnerDep) -> SiteService:
        return SiteService(companies, repo, runner, SiteBuilder(fake_llm, session_factory))

    # Сбрасывается вместе с остальными переопределениями в фикстуре fake_llm.
    app.dependency_overrides[get_site_service] = sites
    return fake_llm


async def _approved_company(client: AsyncClient) -> dict:
    job = await _generate(client, scale="small")
    company_id = job["result_id"]
    response = await client.post(f"/api/v1/companies/{company_id}/approve")
    assert response.status_code == 200, response.text
    return response.json()


async def _build(client: AsyncClient, company_id: str, **body) -> dict:
    response = await client.post(f"/api/v1/companies/{company_id}/sites", json=body)
    assert response.status_code == 202, response.text
    await job_runner.wait_all()
    job = (await client.get(f"/api/v1/jobs/{response.json()['id']}")).json()
    assert job["status"] == "succeeded", job
    return (await client.get(f"/api/v1/sites/{job['result_id']}")).json()


async def test_site_build_preview_and_download(client: AsyncClient, site_llm: FakeLLM):
    company = await _approved_company(client)
    profile = company["profile"]

    site = await _build(client, company["id"], language="ru", theme="nordlicht")

    assert site["status"] == "ready", site["issues"]
    assert [i for i in site["issues"] if i["severity"] == "error"] == []
    assert site["pages"] == ["index.html", "product.html", "company.html"]
    assert site["number"] == 1

    home = await client.get(f"/preview/{site['id']}/index.html")
    assert home.status_code == 200
    html = home.text
    assert profile["contacts"]["phone_display"] in html
    assert profile["brand"]["legal_name"] in html
    assert "application/ld+json" in html
    assert "fonts.googleapis.com" not in html

    company_page = (await client.get(f"/preview/{site['id']}/company.html")).text
    for person in profile["team"]:
        assert f"{person['first_name']} {person['last_name']}" in company_page

    for asset in ("robots.txt", "sitemap.xml", "llms.txt", "assets/style.css", "assets/og.png"):
        assert (await client.get(f"/preview/{site['id']}/{asset}")).status_code == 200
    assert "GPTBot" in (await client.get(f"/preview/{site['id']}/robots.txt")).text

    traversal = await client.get(f"/preview/{site['id']}/assets/%2e%2e/%2e%2e/%2e%2e/app.sqlite3")
    assert traversal.status_code == 404

    listing = (await client.get("/api/v1/sites")).json()
    assert site["id"] in {item["id"] for item in listing}
    companies = (await client.get("/api/v1/companies")).json()["items"]
    assert next(c for c in companies if c["id"] == company["id"])["sites_count"] == 1

    archive = await client.get(f"/api/v1/sites/{site['id']}/download")
    assert archive.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(archive.content)).namelist()
    assert any(name.endswith("/index.html") for name in names)
    assert any("/assets/team/" in name for name in names)
    assert all(
        b"sk-or-test" not in zipfile.ZipFile(io.BytesIO(archive.content)).read(n) for n in names
    )


async def test_german_site_translates_texts_but_keeps_facts(
    client: AsyncClient, site_llm: FakeLLM
):
    company = await _approved_company(client)

    site = await _build(client, company["id"], language="de", theme="mittelstand")

    assert site["status"] == "ready", site["issues"]
    assert site_llm.calls.count("TranslationDraft") == 4
    html = (await client.get(f"/preview/{site['id']}/product.html")).text
    assert '<html lang="de">' in html
    assert "Übersetzung" in html
    assert company["profile"]["contacts"]["email"] in html


async def test_rebuild_reuses_texts_for_free(client: AsyncClient, site_llm: FakeLLM):
    company = await _approved_company(client)
    first = await _build(client, company["id"], language="ru")
    calls_before = len(site_llm.calls)

    second = await _build(client, company["id"], language="ru", theme="graphit", accent="#8a2be2")

    assert len(site_llm.calls) == calls_before
    assert second["number"] == 2
    assert second["reused_from"] == first["id"]
    assert second["cost_usd"] == 0


async def test_edit_marks_old_site_stale_and_blocks_new_build(
    client: AsyncClient, site_llm: FakeLLM
):
    company = await _approved_company(client)
    site = await _build(client, company["id"], language="ru")

    profile = company["profile"]
    profile["brand"]["tagline"] = "Новый слоган после сборки сайта"
    await client.put(
        f"/api/v1/companies/{company['id']}/profile",
        json={"profile": profile, "revision": company["revision"]},
    )

    old = (await client.get(f"/api/v1/sites/{site['id']}")).json()
    assert old["stale"] is True
    html = (await client.get(f"/preview/{site['id']}/index.html")).text
    assert "Новый слоган после сборки сайта" not in html

    response = await client.post(f"/api/v1/companies/{company['id']}/sites", json={})
    assert response.status_code == 409


async def test_unknown_theme_rejected(client: AsyncClient, site_llm: FakeLLM):
    company = await _approved_company(client)

    response = await client.post(
        f"/api/v1/companies/{company['id']}/sites", json={"theme": "neon"}
    )

    assert response.status_code == 400
