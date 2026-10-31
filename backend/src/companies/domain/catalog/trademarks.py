"""
Известные бренды: сгенерированная компания не должна выдавать себя за реальную.
Список не исчерпывающий, это защита от очевидных случаев, а не юридическая проверка.
"""

import re

KNOWN_BRANDS: frozenset[str] = frozenset(
    {
        # Финансы и данные
        "allianz",
        "axa",
        "barclays",
        "blackrock",
        "bloomberg",
        "bnp",
        "citi",
        "citigroup",
        "commerzbank",
        "deka",
        "deutsche bank",
        "dws",
        "factset",
        "fidelity",
        "goldman",
        "hsbc",
        "ing",
        "jpmorgan",
        "kpmg",
        "lseg",
        "mckinsey",
        "moodys",
        "moody's",
        "morgan stanley",
        "morningstar",
        "msci",
        "munich re",
        "pimco",
        "refinitiv",
        "s&p",
        "santander",
        "schroders",
        "ubs",
        "union investment",
        "vanguard",
        "deloitte",
        "pwc",
        "ey",
        "ernst & young",
        "accenture",
        "bafin",
        "boerse",
        "börse",
        "deutsche börse",
        "xetra",
        "sparkasse",
        "volksbank",
        "n26",
        "klarna",
        "paypal",
        # Технологии и потребительские бренды
        "adidas",
        "amazon",
        "apple",
        "bmw",
        "bosch",
        "coca-cola",
        "facebook",
        "google",
        "ibm",
        "intel",
        "meta",
        "microsoft",
        "mercedes",
        "netflix",
        "nike",
        "nvidia",
        "openai",
        "anthropic",
        "oracle",
        "puma",
        "samsung",
        "sap",
        "siemens",
        "telekom",
        "tesla",
        "volkswagen",
        "vw",
        "zalando",
    }
)


def find_known_brand(name: str) -> str | None:
    """Возвращает известный бренд, если он входит в название отдельным словом."""

    normalized = f" {re.sub(r'[^a-z0-9&\'äöüß]+', ' ', name.lower())} "
    for brand in KNOWN_BRANDS:
        if f" {brand} " in normalized:
            return brand
    return None
