import random

import pytest

from src.companies.application.generation.facts import (
    GenerationRequest,
    build_facts,
    resolve_params,
    slugify,
)
from src.companies.domain.enums import CompanyScale, TeamRole
from src.shared.domain.exceptions import BadRequestError


def facts_for(seed: int, **request):
    rng = random.Random(seed)  # noqa: S311
    params = resolve_params(GenerationRequest(**request), rng)
    return build_facts(params, rng)


@pytest.mark.parametrize("seed", range(30))
def test_phone_matches_city_and_reserved_block(seed: int):
    facts = facts_for(seed)
    block = facts.city.phone_block

    assert facts.phone.startswith(f"+49{block.area_code}{block.prefix}")
    assert facts.address.postal_code.startswith(facts.city.postal_prefixes)


@pytest.mark.parametrize("scale", list(CompanyScale))
def test_team_structure(scale: CompanyScale):
    for seed in range(20):
        team = facts_for(seed, scale=scale).team
        roles = [person.role for person in team]

        assert len(team) >= 5
        assert roles.count(TeamRole.CEO) == 1
        assert roles.count(TeamRole.DEPARTMENT_HEAD) == 2
        assert len({person.id for person in team}) == len(team)
        assert len({person.last_name for person in team}) == len(team)
        genders = [person.gender for person in team]
        assert min(genders.count(g) for g in set(genders)) >= 2
        assert len(set(genders)) == 2


def test_user_values_are_kept_and_random_ones_recorded():
    params = facts_for(1, brand_name="Kestrel", scale=CompanyScale.MEDIUM).params

    assert params.brand_name == "Kestrel"
    assert params.scale is CompanyScale.MEDIUM
    assert "scale" not in params.randomized
    assert {"country", "service_type", "model"} <= set(params.randomized)


def test_unknown_service_type_rejected():
    with pytest.raises(BadRequestError):
        facts_for(1, service_type="crypto_signals")


def test_same_params_give_different_companies():
    first, second = facts_for(1, scale=CompanyScale.SMALL), facts_for(2, scale=CompanyScale.SMALL)

    assert first.seeds != second.seeds
    assert {p.full_name for p in first.team} != {p.full_name for p in second.team}


def test_slugify():
    assert slugify("Jörg Weiß") == "joerg-weiss"
    assert slugify("Şahin & Partner") == "sahin-partner"


def test_team_photos_do_not_repeat_clothing_and_pose():
    for seed in range(10):
        team = facts_for(seed, scale=CompanyScale.MEDIUM).team
        poses = [person.appearance.split("Pose: ")[1].split(".")[0] for person in team]
        assert len(set(poses)) == len(poses)


def test_custom_direction_and_service():
    facts = facts_for(3, custom_direction="ИИ для оценки рисков недвижимости")

    assert facts.params.direction == "custom"
    assert facts.params.service_type == "custom"
    assert facts.service_type.name_ru == "ИИ для оценки рисков недвижимости"


def test_custom_service_within_catalog_direction():
    facts = facts_for(
        4, direction="ai_investment_research", custom_service="Разбор отчётов о закупках"
    )

    assert facts.direction.key == "ai_investment_research"
    assert facts.service_type.description == "Разбор отчётов о закупках"


@pytest.mark.parametrize("brand", ["Nike fake", "BlackRock Analytics", "Deutsche Bank Data"])
def test_known_brands_are_rejected(brand: str):
    with pytest.raises(BadRequestError, match="известный бренд"):
        facts_for(1, brand_name=brand)


def test_similar_but_different_brand_is_allowed():
    assert facts_for(1, brand_name="Nikolai Research").params.brand_name == "Nikolai Research"
