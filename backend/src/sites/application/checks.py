"""
Проверки собранного сайта. Факты сверяются по готовым HTML-файлам, а не по
данным шаблона: так ловятся и ошибки шаблона, и подстановки модели.
"""

from typing import Any

import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from src.core.settings import openrouter_config
from src.llm.infra.redaction import redact

from ..domain.enums import SiteLanguage
from ..domain.i18n import FORBIDDEN_PHRASES, HTML_LANG
from .render import PAGES

_PLACEHOLDER_RE = re.compile(
    r"\{\{.*?\}\}|\{%.*?%\}|\{[a-z_]+\}|\[(?:NAME|COMPANY|CITY|TODO)\]"
    r"|\bundefined\b|\bNone\b|\bnull\b|\bTODO\b|Lorem ipsum",
)


_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]{3,}")


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.h1 = 0
        self.title = ""
        self._in_title = False
        self._skip = 0
        self.text: list[str] = []
        self.jsonld: list[str] = []
        self._in_jsonld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        self.tags.append((tag, data))
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._in_title = True
        if tag == "script" and data.get("type") == "application/ld+json":
            self._in_jsonld = True
        elif tag in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
        elif tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._in_jsonld:
            self.jsonld.append(data)
        elif not self._skip:
            self.text.append(data)

    def meta(self, name: str) -> str | None:
        for tag, attrs in self.tags:
            if tag == "meta" and (attrs.get("name") == name or attrs.get("property") == name):
                return attrs.get("content")
        return None

    def links(self, rel: str) -> list[str]:
        return [
            attrs.get("href") or ""
            for tag, attrs in self.tags
            if tag == "link" and rel in (attrs.get("rel") or "").split()
        ]


def _issue(code: str, severity: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "path": path, "message": message}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text)).strip()


MIN_DESCRIPTION, MAX_DESCRIPTION = 70, 180
MAX_TITLE = 70


def _page_meta(  # noqa: C901
    page: str,
    html: str,
    parser: _PageParser,
    language: SiteLanguage,
    brand: str,
) -> list[dict]:
    issues = []
    title = parser.title.strip()
    description = (parser.meta("description") or "").strip()
    if title and brand.lower() not in title.lower():
        issues.append(_issue("title_brand", "error", page, "В title нет названия компании"))
    if len(title) > MAX_TITLE:
        issues.append(
            _issue("title_length", "warning", page, f"title длиной {len(title)} символов")
        )
    if description and not MIN_DESCRIPTION <= len(description) <= MAX_DESCRIPTION:
        issues.append(
            _issue(
                "description_length", "warning", page, f"description: {len(description)} символов"
            )
        )
    if not parser.meta("og:image"):
        issues.append(_issue("og_image", "warning", page, "Нет og:image"))
    issues.extend(
        _issue("img_alt", "error", page, f"У картинки {attrs.get('src')} нет alt")
        for tag, attrs in parser.tags
        if tag == "img" and not (attrs.get("alt") or "").strip()
    )
    if f'<html lang="{HTML_LANG[language]}"' not in html:
        issues.append(_issue("html_lang", "error", page, "Не указан язык страницы"))
    if not parser.title.strip():
        issues.append(_issue("meta_title", "error", page, "Нет title"))
    if not (parser.meta("description") or "").strip():
        issues.append(_issue("meta_description", "error", page, "Нет meta description"))
    if not parser.links("canonical"):
        issues.append(_issue("canonical", "warning", page, "Нет canonical"))
    if not parser.links("icon"):
        issues.append(_issue("favicon", "error", page, "Нет favicon"))
    if parser.h1 != 1:
        issues.append(_issue("h1", "error", page, f"На странице {parser.h1} заголовков h1"))

    hrefs = {attrs.get("href") for tag, attrs in parser.tags if tag == "a"}
    issues.extend(
        _issue("nav", "error", page, f"Нет ссылки на {target}")
        for target in PAGES
        if target not in hrefs
    )
    return issues


def _page_content(
    page: str,
    text: str,
    parser: _PageParser,
    facts: dict[str, str],
    language: SiteLanguage,
) -> list[dict]:
    issues = [
        _issue("fact_missing", "error", page, f"На странице нет факта «{label}»: {value}")
        for label, value in facts.items()
        if _normalize(value) not in text
    ]

    if any(tag in {"form", "input", "textarea", "button"} for tag, _ in parser.tags):
        issues.append(
            _issue("form", "error", page, "На сайте форма, хотя отправка форм не реализована")
        )

    lowered = text.lower()
    issues.extend(
        _issue("fake_feature", "error", page, f"Обещание несуществующей функции: «{phrase}»")
        for phrase in FORBIDDEN_PHRASES[language]
        if phrase in lowered
    )

    if language is SiteLanguage.DE and (cyrillic := _CYRILLIC_RE.search(text)):
        fragment = text[max(cyrillic.start() - 20, 0) : cyrillic.start() + 40]
        issues.append(
            _issue(
                "untranslated",
                "error",
                page,
                f"Непереведённый текст на немецком сайте: «{fragment}»",
            )
        )

    if match := _PLACEHOLDER_RE.search(text):
        issues.append(
            _issue("placeholder", "error", page, f"Незаменённая переменная: {match.group(0)!r}")
        )
    return issues


def _page_links(page: str, site_dir: Path, parser: _PageParser) -> list[dict]:
    """Внутренние ссылки и файлы, на которые ссылается страница, существуют."""

    issues = []
    for tag, attrs in parser.tags:
        ref = attrs.get("href") if tag in {"a", "link"} else attrs.get("src")
        if not ref or re.match(r"^(https?:|mailto:|tel:|#|data:)", ref):
            continue
        local = ref.split("#")[0].split("?")[0]
        if local and not (site_dir / local).exists():
            issues.append(_issue("broken_link", "error", page, f"Битая ссылка: {ref}"))
    return issues


def _page_jsonld(page: str, parser: _PageParser, phone: str) -> list[dict]:
    issues = []
    types = []
    for raw in parser.jsonld:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            issues.append(_issue("jsonld", "error", page, "Некорректная разметка schema.org"))
            continue
        types.append(data.get("@type"))
        if data.get("@type") == "Organization" and data.get("telephone") != phone:
            issues.append(_issue("jsonld_phone", "error", page, "Телефон в schema.org другой"))
    if "Organization" not in types:
        issues.append(_issue("jsonld_org", "error", page, "Нет разметки Organization"))
    return issues


def _team(site_dir: Path, snapshot: dict[str, Any]) -> list[dict]:
    """Каждый человек из карточки - на странице компании и с фото."""

    page = site_dir / "company.html"
    html = unescape(page.read_text(encoding="utf-8")) if page.exists() else ""
    issues = []
    for person in snapshot["team"]:
        name = f"{person['first_name']} {person['last_name']}"
        if name not in html:
            issues.append(_issue("team_member", "error", "company.html", f"Нет сотрудника {name}"))
        if not (site_dir / "assets" / "team" / f"{person['id']}.jpg").exists():
            issues.append(
                _issue("team_photo", "error", "company.html", f"Нет фото сотрудника {name}")
            )
    return issues


def _files(site_dir: Path) -> list[dict]:
    required = (
        "assets/favicon.svg",
        "assets/style.css",
        "assets/og.png",
        "robots.txt",
        "sitemap.xml",
        "llms.txt",
    )
    issues = [
        _issue("asset_missing", "error", path, "Файл не собран")
        for path in required
        if not (site_dir / path).exists()
    ]

    # Ключ не должен оказаться ни в одном файле сайта.
    secret = openrouter_config.api_key.get_secret_value()
    for file in site_dir.rglob("*"):
        if not file.is_file() or file.suffix not in {".html", ".css", ".xml", ".txt", ".svg"}:
            continue
        content = file.read_text(encoding="utf-8", errors="ignore")
        if (secret and secret in content) or redact(content) != content:
            issues.append(
                _issue(
                    "secret", "error", str(file.relative_to(site_dir)), "В файле найден API-ключ"
                )
            )
    return issues


def check_site(
    site_dir: Path,
    *,
    snapshot: dict[str, Any],
    language: SiteLanguage,
) -> list[dict[str, str]]:
    brand, contacts = snapshot["brand"], snapshot["contacts"]
    address = contacts["address"]

    # Факты, которые должны совпадать на всех страницах.
    facts = {
        "юрлицо": brand["legal_name"],
        "телефон": contacts["phone_display"],
        "почта": contacts["email"],
        "улица": f"{address['street']} {address['house_number']}",
        "индекс и город": f"{address['postal_code']} {address['city']}",
    }

    issues: list[dict[str, str]] = []
    for page in PAGES:
        path = site_dir / page
        if not path.exists():
            issues.append(_issue("page_missing", "error", page, "Страница не собрана"))
            continue

        html = path.read_text(encoding="utf-8")
        parser = _PageParser()
        parser.feed(html)
        text = _normalize(" ".join(parser.text))

        issues += _page_meta(page, html, parser, language, brand["name"])
        issues += _page_links(page, site_dir, parser)
        issues += _page_content(page, text, parser, facts, language)
        issues += _page_jsonld(page, parser, contacts["phone"])

    return [*issues, *_team(site_dir, snapshot), *_files(site_dir)]
