"""
Тексты карточки, которые попадают на сайт. Для русской версии они берутся из
карточки как есть, для немецкой переводятся по тем же путям. Имена, телефоны,
адреса и почта не переводятся: шаблон берёт их прямо из снимка карточки.
"""

from typing import Any

import re

TEXT_GROUPS = ("company", "product", "faq", "team")

_DIGITS_RE = re.compile(r"\d+")
_LATIN_RE = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-z0-9ÄÖÜäöüß&+.\-]*[A-Za-z0-9]")


def translatable_texts(profile: dict[str, Any]) -> dict[str, dict[str, str]]:  # noqa: C901
    """Тексты карточки по группам: группа -> {путь: текст}."""

    company: dict[str, str] = {
        "brand.tagline": profile["brand"]["tagline"],
        "contacts.office_hours": profile["contacts"]["office_hours"],
        "history.founding_story": profile["history"]["founding_story"],
        "history.specialization": profile["history"]["specialization"],
        "audience.client_problem": profile["audience"]["client_problem"],
    }
    for index, item in enumerate(profile["history"]["milestones"]):
        company[f"history.milestones[{index}].title"] = item["title"]
        company[f"history.milestones[{index}].description"] = item["description"]
    for index, item in enumerate(profile["audience"]["segments"]):
        company[f"audience.segments[{index}].name"] = item["name"]
        company[f"audience.segments[{index}].description"] = item["description"]

    product_data = profile["product"]
    product: dict[str, str] = {
        "product.summary": product_data["summary"],
        "product.delivery": product_data["delivery"],
    }
    for key in ("inputs", "outputs", "limitations"):
        for index, text in enumerate(product_data[key]):
            product[f"product.{key}[{index}]"] = text
    for key in ("process", "benefits"):
        for index, item in enumerate(product_data[key]):
            product[f"product.{key}[{index}].title"] = item["title"]
            product[f"product.{key}[{index}].description"] = item["description"]

    faq: dict[str, str] = {}
    for index, item in enumerate(profile["faq"]):
        faq[f"faq[{index}].question"] = item["question"]
        faq[f"faq[{index}].answer"] = item["answer"]

    team: dict[str, str] = {}
    for index, person in enumerate(profile["team"]):
        team[f"team[{index}].position"] = person["position"]
        if person.get("department"):
            team[f"team[{index}].department"] = person["department"]
        team[f"team[{index}].bio"] = person["bio"]
        team[f"team[{index}].education"] = person["education"]
        for position, text in enumerate(person["experience"]):
            team[f"team[{index}].experience[{position}]"] = text

    return {"company": company, "product": product, "faq": faq, "team": team}


def all_texts(profile: dict[str, Any]) -> dict[str, str]:
    return {
        path: text
        for group in translatable_texts(profile).values()
        for path, text in group.items()
    }


def numbers(text: str) -> list[str]:
    return sorted(_DIGITS_RE.findall(text))


def latin_terms(text: str) -> set[str]:
    """Имена, бренды и термины латиницей: в переводе они должны сохраниться."""

    return {match.lower() for match in _LATIN_RE.findall(text) if len(match) > 1}


def facts_numbers(profile: dict[str, Any]) -> set[str]:
    """Все числа карточки: тексты сайта не должны добавлять новых."""

    found: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, str):
            found.update(_DIGITS_RE.findall(value))
        elif isinstance(value, bool):
            return
        elif isinstance(value, int | float):
            found.add(str(value))
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(profile)
    return found
