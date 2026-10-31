from typing import Any, Self

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.shared.domain.entities import AggregateRoot

from .enums import SiteLanguage, SiteStatus


@dataclass(kw_only=True)
class SiteVersion(AggregateRoot):
    """
    Собранная версия сайта. Хранит снимок карточки той ревизии, из которой собрана:
    правки карточки не меняют уже созданные версии, для них собирается новая.
    """

    company_id: UUID
    company_revision: int
    number: int
    language: SiteLanguage
    theme: str
    accent: str | None = None
    status: SiteStatus = SiteStatus.READY
    snapshot: dict[str, Any] = field(default_factory=dict)
    content: dict[str, Any] = field(default_factory=dict)
    issues: list[dict[str, str]] = field(default_factory=list)
    pages: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    requests: int = 0
    reused_from: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        site_id: UUID | None = None,
        company_id: UUID,
        company_revision: int,
        number: int,
        language: SiteLanguage,
        theme: str,
        accent: str | None,
        snapshot: dict[str, Any],
        content: dict[str, Any],
        issues: list[dict[str, str]],
        pages: list[str],
        cost_usd: float,
        requests: int,
        reused_from: UUID | None,
    ) -> Self:
        has_errors = any(issue["severity"] == "error" for issue in issues)
        return cls(
            id=site_id or uuid4(),
            company_id=company_id,
            company_revision=company_revision,
            number=number,
            language=language,
            theme=theme,
            accent=accent,
            status=SiteStatus.FAILED_CHECKS if has_errors else SiteStatus.READY,
            snapshot=snapshot,
            content=content,
            issues=issues,
            pages=pages,
            cost_usd=round(cost_usd, 6),
            requests=requests,
            reused_from=reused_from,
        )
