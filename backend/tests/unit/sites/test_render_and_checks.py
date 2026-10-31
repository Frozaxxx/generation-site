import json
import re
import uuid
from pathlib import Path

import pytest

from src.companies.domain.serialization import profile_to_dict
from src.shared.domain.exceptions import BadRequestError
from src.sites.application.checks import check_site
from src.sites.application.drafts import SiteCopyDraft, TranslationDraft
from src.sites.application.render import SiteRenderer, initials
from src.sites.application.texts import all_texts
from src.sites.domain.enums import SiteLanguage
from src.sites.domain.themes import THEMES, get_theme
from tests.support.factories import make_profile

META = {"title": "Kestrel Data: обзоры отчётности", "description": "x" * 140}
COPY_KEYS = [
    "hero_title",
    "hero_lead",
    "audience_lead",
    "benefits_lead",
    "process_lead",
    "cta_title",
    "cta_text",
    "product_lead",
    "limitations_lead",
    "company_lead",
    "team_lead",
]
COPY = {
    "home": META,
    "product": META,
    "company": META,
    **dict.fromkeys(
        COPY_KEYS, "Текст подачи без выдуманных чисел и фактов, только по карточке компании."
    ),
}


def render(tmp_path: Path, language: SiteLanguage, theme: str = "kontor") -> tuple[Path, dict]:
    snapshot = profile_to_dict(make_profile())
    out = tmp_path / "site"
    SiteRenderer(out).render(
        company_id=uuid.uuid4(),
        snapshot=snapshot,
        texts=all_texts(snapshot),
        copy_text=COPY,
        language=language,
        theme=get_theme(theme),
    )
    return out, snapshot


def codes(issues: list[dict]) -> set[str]:
    # Фото в фабрике нет: эти ошибки ожидаемы и здесь не проверяются.
    return {issue["code"] for issue in issues if issue["code"] != "team_photo"}


@pytest.mark.parametrize("theme", list(THEMES))
def test_every_theme_renders_clean_site(tmp_path: Path, theme: str):
    out, snapshot = render(tmp_path, SiteLanguage.RU, theme)

    assert codes(check_site(out, snapshot=snapshot, language=SiteLanguage.RU)) == set()
    css = (out / "assets" / "style.css").read_text(encoding="utf-8")
    assert "@font-face" in css
    assert "googleapis" not in css
    for face in re.findall(r'url\("([^"]+)"\)', css):
        assert (out / "assets" / face).exists()


def test_seo_and_ai_files(tmp_path: Path):
    out, snapshot = render(tmp_path, SiteLanguage.RU)
    html = (out / "index.html").read_text(encoding="utf-8")

    assert '<meta name="robots" content="index, follow' in html
    assert '<link rel="canonical" href="https://kestrel-data.de/">' in html
    blocks = re.findall(r'<script type="application/ld\+json">\n(.*?)\n</script>', html, re.DOTALL)
    types = {json.loads(block)["@type"] for block in blocks}
    assert {"Organization", "WebSite", "WebPage"} <= types

    llms = (out / "llms.txt").read_text(encoding="utf-8")
    assert llms.startswith("# Kestrel Data")
    assert snapshot["contacts"]["phone_display"] in llms
    assert "ClaudeBot" in (out / "robots.txt").read_text(encoding="utf-8")


def test_untranslated_german_site_is_caught(tmp_path: Path):
    out, snapshot = render(tmp_path, SiteLanguage.DE)

    assert "untranslated" in codes(check_site(out, snapshot=snapshot, language=SiteLanguage.DE))


def test_changed_phone_in_html_is_caught(tmp_path: Path):
    out, snapshot = render(tmp_path, SiteLanguage.RU)
    page = out / "product.html"
    page.write_text(
        page.read_text(encoding="utf-8").replace(snapshot["contacts"]["phone_display"], "+49 1"),
        encoding="utf-8",
    )

    issues = check_site(out, snapshot=snapshot, language=SiteLanguage.RU)
    assert any(i["code"] == "fact_missing" and i["path"] == "product.html" for i in issues)


def test_form_and_broken_link_are_caught(tmp_path: Path):
    out, snapshot = render(tmp_path, SiteLanguage.RU)
    page = out / "index.html"
    html = page.read_text(encoding="utf-8").replace(
        "</main>", '<form><input type="file"></form><a href="missing.html">x</a></main>'
    )
    page.write_text(html, encoding="utf-8")

    found = codes(check_site(out, snapshot=snapshot, language=SiteLanguage.RU))
    assert {"form", "broken_link"} <= found


def test_copy_cannot_invent_numbers_or_drop_brand():
    schema = SiteCopyDraft.with_facts({"2019", "18"}, "Kestrel Data")

    with pytest.raises(ValueError, match="числа, которых нет"):
        schema.model_validate(
            {**COPY, "hero_lead": "Более 200 клиентов доверяют нам свои данные и получают обзоры."}
        )
    with pytest.raises(ValueError, match="нет названия бренда"):
        schema.model_validate({**COPY, "home": {**META, "title": "Обзоры отчётности для фондов"}})


def test_translation_must_keep_numbers_and_names():
    schema = TranslationDraft.for_texts({"a": "Основана в 2019 году, руководит Lena Hartmann"})

    assert (
        schema.model_validate({"items": {"a": "Gegründet 2019, geleitet von Lena Hartmann"}})
        .items["a"]
        .startswith("Gegründet")
    )
    with pytest.raises(ValueError, match="числа"):
        schema.model_validate({"items": {"a": "Gegründet 2018, geleitet von Lena Hartmann"}})
    with pytest.raises(ValueError, match="имена"):
        schema.model_validate({"items": {"a": "Gegründet 2019 von der Gründerin"}})


def test_accent_override():
    assert get_theme("kontor", "#FFCC00").accent_ink == "#111418"
    with pytest.raises(BadRequestError):
        get_theme("kontor", "red")


def test_initials():
    assert initials("GridQuant") == "GQ"
    assert initials("Nordlicht Research") == "NR"
