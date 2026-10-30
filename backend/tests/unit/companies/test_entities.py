import pytest

from src.companies.domain.checks import check_profile
from src.companies.domain.enums import CompanyStatus
from src.shared.domain.exceptions import InvariantViolationError
from tests.support.factories import make_company, make_profile, profile_data


def test_new_company_is_draft():
    company = make_company()

    assert company.status is CompanyStatus.DRAFT
    assert company.revision == 1


def test_edit_increments_revision_and_resets_approval():
    company = make_company()
    company.approve(check_profile(company.profile, "DE"))
    assert company.is_approved

    data = profile_data()
    data["brand"]["tagline"] = "Новая формулировка позиционирования"
    changed = company.edit(make_profile(data))

    assert changed
    assert company.revision == 2
    assert company.status is CompanyStatus.DRAFT
    assert company.approved_at is None


def test_edit_without_changes_keeps_revision():
    company = make_company()

    assert not company.edit(make_profile())
    assert company.revision == 1


def test_approve_with_errors_is_rejected():
    data = profile_data()
    data["faq"] = data["faq"][:3]
    company = make_company(make_profile(data))

    with pytest.raises(InvariantViolationError) as error:
        company.approve(check_profile(company.profile, "DE"))

    assert any(item["code"] == "faq_size" for item in error.value.details)
    assert company.status is CompanyStatus.DRAFT
