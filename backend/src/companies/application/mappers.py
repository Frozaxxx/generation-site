from typing import Any

from dataclasses import asdict

from ..domain.checks import Issue, check_profile
from ..domain.entities import Company
from ..domain.enums import IssueSeverity
from ..domain.serialization import profile_to_dict
from .dtos import CompanyListItem, CompanyRead, IssueRead


def to_list_item(company: Company) -> CompanyListItem:
    profile = company.profile
    return CompanyListItem(
        id=company.id,
        brand_name=profile.brand.name,
        legal_name=profile.brand.legal_name,
        city=profile.contacts.address.city,
        service_type=company.params.service_type,
        scale=company.params.scale,
        status=company.status,
        revision=company.revision,
        team_size=len(profile.team),
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def to_read(company: Company, issues: list[Issue] | None = None) -> CompanyRead:
    if issues is None:
        issues = check_profile(company.profile, company.params.country)
    issues = [*issues, *review_issues(company)]

    return CompanyRead(
        id=company.id,
        status=company.status,
        revision=company.revision,
        params=_params_dict(company),
        profile=profile_to_dict(company.profile),
        generation=asdict(company.generation) if company.generation else None,
        issues=[IssueRead.model_validate(issue.as_dict()) for issue in issues],
        created_at=company.created_at,
        updated_at=company.updated_at,
        approved_at=company.approved_at,
    )


def review_issues(company: Company) -> list[Issue]:
    """
    Замечания смысловой проверки моделью. Показываем их только для той ревизии, которую
    проверяли, и как предупреждения: окончательное решение за человеком.
    """

    info = company.generation
    if info is None or info.review_revision != company.revision:
        return []
    return [
        Issue(
            code=f"review_{item.get('severity', 'warning')}",
            severity=IssueSeverity.WARNING,
            path=item.get("path", ""),
            message=f"Смысловая проверка: {item.get('message', '')}",
        )
        for item in info.review
    ]


def to_export(company: Company) -> dict[str, Any]:
    """Данные компании для скачивания: только факты, без служебных и секретных полей."""

    return {
        "id": str(company.id),
        "status": company.status.value,
        "revision": company.revision,
        "params": _params_dict(company),
        "profile": profile_to_dict(company.profile),
        "created_at": company.created_at.isoformat(),
        "updated_at": company.updated_at.isoformat(),
    }


def _params_dict(company: Company) -> dict[str, Any]:
    params = asdict(company.params)
    params["randomized"] = list(company.params.randomized)
    return params
