"""
Сборка статического сайта из снимка карточки, текстов и темы.
"""

from typing import Any

import copy
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from PIL import Image, ImageDraw, ImageFont

from src.companies.application.generation.photos import company_media_dir
from src.shared.utils.time import current_datetime

from ..domain.enums import SiteLanguage
from ..domain.i18n import HTML_LANG, OG_LOCALE, UI
from ..domain.themes import Theme

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
FONTS_DIR = Path(__file__).resolve().parent.parent / "static" / "fonts"
FONT_SUBSETS = ("latin", "cyrillic")
# Краулеры поисковиков и ИИ-ассистентов, которым сайт явно открыт.
CRAWLERS = (
    "Googlebot",
    "Bingbot",
    "YandexBot",
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "Claude-SearchBot",
    "PerplexityBot",
    "Google-Extended",
    "Applebot-Extended",
)
PAGES = ("index.html", "product.html", "company.html")
PAGE_KEYS = {"index.html": "home", "product.html": "product", "company.html": "company"}

_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n|\n", text or "") if part.strip()]


def _jsonld(data: dict[str, Any]) -> Markup:
    raw = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return Markup(f'<script type="application/ld+json">\n{raw}\n</script>')  # noqa: S704


_env.filters["paragraphs"] = _paragraphs
_env.filters["jsonld"] = _jsonld


def _set_path(data: Any, path: str, value: str) -> None:
    keys = [int(part) if part.isdigit() else part for part in re.split(r"\.|\[|\]", path) if part]
    node = data
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value


def localized_profile(snapshot: dict[str, Any], texts: dict[str, str]) -> dict[str, Any]:
    profile = copy.deepcopy(snapshot)
    for path, text in texts.items():
        _set_path(profile, path, text)
    return profile


def initials(brand: str) -> str:
    """Монограмма: первые буквы двух слов или заглавные слитного названия (GridQuant -> GQ)."""

    words = [word for word in re.split(r"[\s\-]+", brand) if word]
    if len(words) > 1:
        return "".join(word[0] for word in words[:2]).upper()
    capitals = [char for char in brand if char.isupper()]
    return ("".join(capitals[:2]) if len(capitals) > 1 else brand[:2]).upper()


@dataclass(frozen=True, slots=True)
class RenderResult:
    pages: list[str]
    files: list[str]


class SiteRenderer:
    def __init__(self, output_dir: Path) -> None:
        self._out = output_dir

    def render(
        self,
        *,
        company_id: Any,
        snapshot: dict[str, Any],
        texts: dict[str, str],
        copy_text: dict[str, Any],
        language: SiteLanguage,
        theme: Theme,
    ) -> RenderResult:
        if self._out.exists():
            shutil.rmtree(self._out)
        (self._out / "assets" / "team").mkdir(parents=True)

        profile = localized_profile(snapshot, texts)
        brand = profile["brand"]
        base_url = f"https://{brand['domain']}"
        ui = UI[language]

        team = self._copy_photos(company_id, profile["team"])
        self._write_brand_assets(brand["name"], theme)
        font_faces = self._copy_fonts(theme)
        preload_subset = "cyrillic" if language is SiteLanguage.RU else "latin"
        preload_font = f"assets/fonts/{theme.body_package}-{preload_subset}-400-normal.woff2"

        organization = self._organization(profile, base_url, ui)
        context = {
            "lang": HTML_LANG[language],
            "og_locale": OG_LOCALE[language],
            "ui": ui,
            "theme": asdict(theme),
            "brand": brand,
            "initials": initials(brand["name"]),
            "contacts": profile["contacts"],
            "address": profile["contacts"]["address"],
            "history": profile["history"],
            "audience": profile["audience"],
            "product": profile["product"],
            "faq": profile["faq"],
            "team": team,
            "ceo": next((person for person in team if person["role"] == "ceo"), None),
            "copy": copy_text,
            "base_url": base_url,
            "preload_font": preload_font,
            "year": current_datetime().year,
            "nav": [
                ("index.html", ui["nav_home"]),
                ("product.html", ui["nav_product"]),
                ("company.html", ui["nav_company"]),
            ],
        }

        jsonld = {
            "index.html": [organization, self._website(profile, base_url, language)],
            "product.html": [
                organization,
                self._service(profile, base_url),
                self._faq_page(profile),
                self._breadcrumbs(base_url, ui, "product.html", ui["nav_product"]),
            ],
            "company.html": [
                organization,
                self._about(base_url, team),
                self._breadcrumbs(base_url, ui, "company.html", ui["nav_company"]),
            ],
        }

        today = current_datetime().date().isoformat()
        for page in PAGES:
            meta = copy_text[PAGE_KEYS[page]]
            canonical = base_url + ("/" if page == "index.html" else f"/{page}")
            webpage = self._webpage(page, meta, canonical, base_url, language, today)
            html = _env.get_template(f"site/{page}").render(
                **context,
                page=page,
                meta=meta,
                canonical=canonical,
                jsonld=[*jsonld[page], webpage],
            )
            (self._out / page).write_text(html, encoding="utf-8")

        css = _env.get_template("site/style.css").render(
            theme=asdict(theme), font_faces=font_faces
        )
        (self._out / "assets" / "style.css").write_text(_minify_css(css), encoding="utf-8")
        robots = "".join(f"User-agent: {bot}\nAllow: /\n\n" for bot in CRAWLERS)
        robots += f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n"
        (self._out / "robots.txt").write_text(robots, encoding="utf-8")
        (self._out / "llms.txt").write_text(
            _env.get_template("site/llms.txt").render(**context), encoding="utf-8"
        )
        (self._out / "sitemap.xml").write_text(
            _env.get_template("site/sitemap.xml").render(
                base_url=base_url, date=current_datetime().date().isoformat()
            ),
            encoding="utf-8",
        )

        files = sorted(
            str(path.relative_to(self._out)).replace("\\", "/")
            for path in self._out.rglob("*")
            if path.is_file()
        )
        return RenderResult(pages=list(PAGES), files=files)

    # ------------------------------------------------------------------
    # Файлы
    # ------------------------------------------------------------------

    def _copy_photos(self, company_id: Any, team: list[dict[str, Any]]) -> list[dict[str, Any]]:
        people = []
        for source_person in team:
            person = dict(source_person)
            person["full_name"] = f"{person['first_name']} {person['last_name']}"
            photo = person.get("photo")
            if photo:
                source = company_media_dir(company_id) / photo["file"]
                if source.exists():
                    target = f"assets/team/{person['id']}.jpg"
                    shutil.copyfile(source, self._out / target)
                    person["photo_src"] = target
            people.append(person)
        return people

    def _copy_fonts(self, theme: Theme) -> list[dict[str, Any]]:
        """Копирует woff2 нужных начертаний и возвращает описания @font-face."""

        ranges = json.loads((FONTS_DIR / "unicode-ranges.json").read_text(encoding="utf-8"))
        target = self._out / "assets" / "fonts"
        target.mkdir(parents=True, exist_ok=True)

        faces = []
        for font in theme.fonts:
            shutil.copyfile(
                FONTS_DIR / f"{font.package}.LICENSE.txt", target / f"{font.package}.LICENSE.txt"
            )
            for weight in font.weights:
                for subset in FONT_SUBSETS:
                    name = f"{font.package}-{subset}-{weight}-normal.woff2"
                    shutil.copyfile(FONTS_DIR / name, target / name)
                    faces.append(
                        {
                            "family": font.family,
                            "weight": weight,
                            "src": f"fonts/{name}",
                            "range": ranges[font.package][subset],
                        }
                    )
        return faces

    def _write_brand_assets(self, brand: str, theme: Theme) -> None:
        letters = initials(brand)
        radius = "0" if theme.radius == "0px" else "7"
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            f'<rect width="32" height="32" rx="{radius}" fill="{theme.accent}"/>'
            f'<text x="16" y="21.5" text-anchor="middle" font-family="Arial, sans-serif" '
            f'font-size="14" font-weight="700" fill="{theme.accent_ink}">{letters}</text></svg>'
        )
        (self._out / "assets" / "favicon.svg").write_text(svg, encoding="utf-8")

        for size, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png")):
            self._monogram(letters, theme, size).save(self._out / "assets" / name, format="PNG")
        self._og_image(brand, theme).save(self._out / "assets" / "og.png", format="PNG")

    @staticmethod
    def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:  # старый Pillow без векторного шрифта по умолчанию
            return ImageFont.load_default()

    def _monogram(self, letters: str, theme: Theme, size: int) -> Image.Image:
        image = Image.new("RGB", (size, size), theme.accent)
        draw = ImageDraw.Draw(image)
        font = self._font(int(size * 0.46))
        draw.text((size / 2, size / 2), letters, fill=theme.accent_ink, font=font, anchor="mm")
        return image

    def _og_image(self, brand: str, theme: Theme) -> Image.Image:
        image = Image.new("RGB", (1200, 630), theme.background)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1200, 18), fill=theme.accent)
        draw.text((80, 315), brand, fill=theme.ink, font=self._font(96), anchor="lm")
        draw.rectangle((80, 400, 260, 408), fill=theme.accent)
        return image

    # ------------------------------------------------------------------
    # schema.org
    # ------------------------------------------------------------------

    @staticmethod
    def _postal_address(profile: dict[str, Any]) -> dict[str, Any]:
        address = profile["contacts"]["address"]
        return {
            "@type": "PostalAddress",
            "streetAddress": f"{address['street']} {address['house_number']}",
            "postalCode": address["postal_code"],
            "addressLocality": address["city"],
            "addressRegion": address["state"],
            "addressCountry": address["country_code"],
        }

    @staticmethod
    def _person(person: dict[str, Any], base_url: str) -> dict[str, Any]:
        data = {
            "@type": "Person",
            "name": f"{person['first_name']} {person['last_name']}",
            "jobTitle": person["position"],
        }
        if person.get("photo_src"):
            data["image"] = f"{base_url}/{person['photo_src']}"
        return data

    def _organization(self, profile: dict[str, Any], base_url: str, ui: dict[str, str]) -> dict:
        brand, contacts = profile["brand"], profile["contacts"]
        ceo = next((p for p in profile["team"] if p["role"] == "ceo"), None)
        data: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{base_url}/#organization",
            "name": brand["name"],
            "legalName": brand["legal_name"],
            "url": f"{base_url}/",
            "logo": f"{base_url}/assets/apple-touch-icon.png",
            "slogan": brand["tagline"],
            "email": contacts["email"],
            "telephone": contacts["phone"],
            "address": self._postal_address(profile),
            "foundingDate": str(profile["history"]["founded_year"]),
            "numberOfEmployees": {
                "@type": "QuantitativeValue",
                "value": profile["history"]["employees"],
            },
            "areaServed": ui["country_DE"],
            "alternateName": brand["legal_name"],
            "description": profile["product"]["summary"][:300],
            "knowsAbout": [
                profile["product"]["name"],
                *[segment["name"] for segment in profile["audience"]["segments"]],
            ],
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "customer support",
                "telephone": contacts["phone"],
                "email": contacts["email"],
                "areaServed": profile["contacts"]["address"]["country_code"],
            },
        }
        if ceo:
            data["founder"] = {
                "@type": "Person",
                "name": f"{ceo['first_name']} {ceo['last_name']}",
            }
        return data

    @staticmethod
    def _webpage(
        _page: str,
        meta: dict[str, str],
        canonical: str,
        base_url: str,
        language: SiteLanguage,
        today: str,
    ) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": f"{canonical}#webpage",
            "url": canonical,
            "name": meta["title"],
            "description": meta["description"],
            "inLanguage": HTML_LANG[language],
            "isPartOf": {"@id": f"{base_url}/#website"},
            "about": {"@id": f"{base_url}/#organization"},
            "dateModified": today,
        }

    @staticmethod
    def _website(profile: dict[str, Any], base_url: str, language: SiteLanguage) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{base_url}/#website",
            "name": profile["brand"]["name"],
            "alternateName": profile["brand"]["legal_name"],
            "url": f"{base_url}/",
            "inLanguage": HTML_LANG[language],
            "publisher": {"@id": f"{base_url}/#organization"},
        }

    @staticmethod
    def _service(profile: dict[str, Any], base_url: str) -> dict:
        product = profile["product"]
        return {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": product["name"],
            "description": product["summary"],
            "provider": {"@id": f"{base_url}/#organization"},
            "areaServed": profile["contacts"]["address"]["country_code"],
            "audience": [
                {"@type": "BusinessAudience", "name": segment["name"]}
                for segment in profile["audience"]["segments"]
            ],
            "url": f"{base_url}/product.html",
        }

    @staticmethod
    def _faq_page(profile: dict[str, Any]) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                }
                for item in profile["faq"]
            ],
        }

    def _about(self, base_url: str, team: list[dict[str, Any]]) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "url": f"{base_url}/company.html",
            "about": {"@id": f"{base_url}/#organization"},
            "mainEntity": {
                "@type": "Organization",
                "@id": f"{base_url}/#organization",
                "employee": [self._person(person, base_url) for person in team],
            },
        }

    @staticmethod
    def _breadcrumbs(base_url: str, ui: dict[str, str], page: str, title: str) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": ui["nav_home"],
                    "item": f"{base_url}/",
                },
                {"@type": "ListItem", "position": 2, "name": title, "item": f"{base_url}/{page}"},
            ],
        }


def _minify_css(css: str) -> str:
    """Простая минификация: комментарии и лишние пробелы."""

    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};:,>])\s*", r"\1", css)
    return css.replace(";}", "}").strip() + "\n"


def zip_site(source_dir: Path, archive: Path, root_name: str) -> Path:
    """Архив с папкой сайта внутри: распаковал - открыл index.html."""

    archive.parent.mkdir(parents=True, exist_ok=True)
    base = archive.with_suffix("")
    staging = source_dir.parent / f".{root_name}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(source_dir, staging / root_name)
    result = shutil.make_archive(str(base), "zip", root_dir=staging)
    shutil.rmtree(staging)
    return Path(result)
