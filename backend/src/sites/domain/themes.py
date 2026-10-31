"""
Темы оформления единого шаблона. Тема задаёт шрифты, палитру и характер формы;
акцентный цвет можно переопределить.
"""

import re
from dataclasses import dataclass, replace

from src.shared.domain.exceptions import BadRequestError

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True, slots=True)
class FontSpec:
    """Шрифт из каталога static/fonts (Fontsource, лицензия OFL)."""

    family: str
    package: str
    weights: tuple[int, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Theme:
    key: str
    name: str
    description: str
    heading_font: str
    body_font: str
    # Шрифты лежат внутри сайта: без запросов к Google (GDPR) и без интернета в архиве.
    fonts: tuple[FontSpec, ...]
    body_package: str
    background: str
    surface: str
    ink: str
    muted: str
    line: str
    accent: str
    accent_ink: str  # текст на акцентном фоне
    radius: str
    heading_weight: int
    heading_tracking: str

    def with_accent(self, accent: str | None) -> Theme:
        if not accent:
            return self
        if not _HEX_RE.match(accent):
            raise BadRequestError("Акцентный цвет задаётся в формате #RRGGBB")
        return replace(self, accent=accent.lower(), accent_ink=_contrast_ink(accent))


def _contrast_ink(hex_color: str) -> str:
    red, green, blue = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "#111418" if luminance > 0.55 else "#ffffff"  # noqa: PLR2004


THEMES: dict[str, Theme] = {
    theme.key: theme
    for theme in (
        Theme(
            key="kontor",
            name="Kontor",
            description="Спокойная деловая подача: антиква в заголовках, стальной синий",
            heading_font="'Source Serif 4', Georgia, serif",
            body_font="'IBM Plex Sans', 'Segoe UI', sans-serif",
            fonts=(
                FontSpec("Source Serif 4", "source-serif-4", (500, 600)),
                FontSpec("IBM Plex Sans", "ibm-plex-sans", (400, 500, 600)),
            ),
            body_package="ibm-plex-sans",
            background="#f5f6f8",
            surface="#ffffff",
            ink="#1b2433",
            muted="#596476",
            line="#dbe0e7",
            accent="#2f5d8a",
            accent_ink="#ffffff",
            radius="3px",
            heading_weight=600,
            heading_tracking="-0.01em",
        ),
        Theme(
            key="nordlicht",
            name="Nordlicht",
            description="Современный гротеск, мягкие скругления, глубокий бирюзовый",
            heading_font="'Manrope', 'Segoe UI', sans-serif",
            body_font="'Manrope', 'Segoe UI', sans-serif",
            fonts=(FontSpec("Manrope", "manrope", (400, 500, 700, 800)),),
            body_package="manrope",
            background="#f2f5f4",
            surface="#ffffff",
            ink="#0f2627",
            muted="#4f6566",
            line="#d5dfdd",
            accent="#0f6f63",
            accent_ink="#ffffff",
            radius="14px",
            heading_weight=800,
            heading_tracking="-0.025em",
        ),
        Theme(
            key="mittelstand",
            name="Mittelstand",
            description="Классика немецкого B2B: PT Serif и PT Sans, оливковый",
            heading_font="'PT Serif', Georgia, serif",
            body_font="'PT Sans', 'Segoe UI', sans-serif",
            fonts=(
                FontSpec("PT Serif", "pt-serif", (400, 700)),
                FontSpec("PT Sans", "pt-sans", (400, 700)),
            ),
            body_package="pt-sans",
            background="#f3f4ee",
            surface="#ffffff",
            ink="#22281d",
            muted="#5b6352",
            line="#d9dccf",
            accent="#4b6a2e",
            accent_ink="#ffffff",
            radius="6px",
            heading_weight=700,
            heading_tracking="0",
        ),
        Theme(
            key="graphit",
            name="Graphit",
            description="Контрастная графика: широкий Unbounded, графит и кобальт",
            heading_font="'Unbounded', 'Segoe UI', sans-serif",
            body_font="'Golos Text', 'Segoe UI', sans-serif",
            fonts=(
                FontSpec("Unbounded", "unbounded", (500, 600)),
                FontSpec("Golos Text", "golos-text", (400, 500, 600)),
            ),
            body_package="golos-text",
            background="#ffffff",
            surface="#f4f5f7",
            ink="#16181c",
            muted="#5d636b",
            line="#e1e3e7",
            accent="#2443b8",
            accent_ink="#ffffff",
            radius="0px",
            heading_weight=600,
            heading_tracking="-0.02em",
        ),
    )
}

DEFAULT_THEME = "kontor"


def get_theme(key: str, accent: str | None = None) -> Theme:
    theme = THEMES.get(key)
    if theme is None:
        raise BadRequestError(f"Неизвестная тема {key!r}", details={"themes": list(THEMES)})
    return theme.with_accent(accent)
