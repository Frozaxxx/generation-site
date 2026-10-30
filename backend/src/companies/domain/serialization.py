from typing import Any

from pydantic import TypeAdapter

from .profile import CompanyProfile

profile_adapter: TypeAdapter[CompanyProfile] = TypeAdapter(CompanyProfile)


def profile_from_dict(data: Any) -> CompanyProfile:
    """Проверяет структуру и типы карточки, бросает `pydantic.ValidationError`."""

    return profile_adapter.validate_python(data)


def profile_to_dict(profile: CompanyProfile) -> dict[str, Any]:
    return profile_adapter.dump_python(profile, mode="json")


def profile_json_schema() -> dict[str, Any]:
    schema = profile_adapter.json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "CompanyProfile"
    schema["description"] = (
        "Карточка компании: единый источник фактов для всех страниц сайта. "
        "Тексты карточки хранятся на русском, сайт может выпускаться на русском или немецком."
    )
    return schema
