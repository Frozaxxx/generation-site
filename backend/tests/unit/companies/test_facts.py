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
