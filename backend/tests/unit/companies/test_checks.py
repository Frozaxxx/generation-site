import pytest

from src.companies.domain.checks import check_profile, errors_only
from src.companies.domain.enums import IssueSeverity
from tests.support.factories import make_profile, profile_data


def _codes(data: dict) -> set[str]:
    return {issue.code for issue in check_profile(make_profile(data), "DE")}


def test_valid_profile_has_no_errors():
    assert errors_only(check_profile(make_profile(), "DE")) == []


def test_phone_must_match_city():
    data = profile_data()
    data["contacts"]["phone"] = "+493023125417"
    data["contacts"]["phone_display"] = "+49 30 23125 417"

    assert "phone_city" in _codes(data)


def test_phone_outside_reserved_block_is_warning():
    data = profile_data()
    data["contacts"]["phone"] = "+496912345678"
    data["contacts"]["phone_display"] = "+49 69 12345678"

    issues = check_profile(make_profile(data), "DE")
    issue = next(issue for issue in issues if issue.code == "phone_unreserved")
    assert issue.severity is IssueSeverity.WARNING


def test_postal_code_must_belong_to_city():
    data = profile_data()
    data["contacts"]["address"]["postal_code"] = "10117"

    assert "postal_code" in _codes(data)


def test_email_domain_must_match_site():
    data = profile_data()
    data["contacts"]["email"] = "info@kestrel.com"

    assert "email_domain" in _codes(data)


@pytest.mark.parametrize("text", ["Обзор для {company_name}", "Привет, [NAME]", "{{ city }}"])
def test_placeholders_are_errors(text: str):
    data = profile_data()
    data["product"]["summary"] = f"{text} - сервис сравнивает отчётность с консенсусом и прошлым."

    assert "placeholder" in _codes(data)


def test_team_needs_ceo_two_heads_and_five_people():
    data = profile_data()
    data["team"] = data["team"][:2]

    assert {"team_size", "team_heads"} <= _codes(data)


def test_faq_needs_exactly_five_items():
    data = profile_data()
    data["faq"] = data["faq"][:4]

    assert "faq_size" in _codes(data)


def test_milestone_before_founding_is_error():
    data = profile_data()
    data["history"]["milestones"][0]["year"] = 2015

    assert "milestone_year" in _codes(data)


def test_unknown_country():
    assert [issue.code for issue in check_profile(make_profile(), "FR")] == ["country_unknown"]
