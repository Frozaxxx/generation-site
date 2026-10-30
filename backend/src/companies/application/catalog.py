from src.core.settings import openrouter_config

from ..domain.catalog import COUNTRIES, DIRECTIONS, SCALES
from .dtos import CatalogOption, CatalogRead


def build_catalog() -> CatalogRead:
    """Справочник для формы генерации."""

    return CatalogRead(
        countries=[
            CatalogOption(key=country.code, label=country.name_ru)
            for country in COUNTRIES.values()
        ],
        directions=[
            CatalogOption(key=item.key, label=item.name_ru, description=item.description)
            for item in DIRECTIONS.values()
        ],
        service_types={
            direction.key: [
                CatalogOption(key=item.key, label=item.name_ru, description=item.description)
                for item in direction.service_types
            ]
            for direction in DIRECTIONS.values()
        },
        scales=[
            CatalogOption(
                key=profile.scale.value,
                label=profile.name_ru,
                description=f"{profile.employees[0]}–{profile.employees[1]} сотрудников",
            )
            for profile in SCALES.values()
        ],
        models=[
            CatalogOption(key=model, label=model)
            for model in openrouter_config.allowed_text_models
        ],
        default_model=openrouter_config.text_model,
    )
