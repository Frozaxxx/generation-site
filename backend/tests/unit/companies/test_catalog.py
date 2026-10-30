import pytest

from src.companies.domain.catalog import GERMANY


@pytest.mark.parametrize("city", GERMANY.cities, ids=lambda city: city.key)
def test_streets_belong_to_city_postal_codes(city):
    for street in city.streets:
        assert street.postal_code.startswith(city.postal_prefixes), street


def test_phone_block_builds_reserved_number():
    block = GERMANY.city("berlin").phone_block

    assert block.number(7) == "23125007"
    with pytest.raises(ValueError, match="outside"):
        block.number(1000)


def test_every_scale_has_legal_forms():
    assert all(GERMANY.legal_forms.values())
