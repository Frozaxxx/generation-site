from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..domain.entities import SiteVersion
from ..domain.enums import SiteLanguage, SiteStatus


class BuildSiteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: SiteLanguage = SiteLanguage.RU
    theme: str = "kontor"
    accent: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    reuse_texts: bool = Field(
        default=True,
        description="Взять тексты прошлой версии с той же ревизией и языком (бесплатно).",
    )
    model: str | None = None
    budget_usd: float | None = Field(default=None, gt=0)


class SiteIssue(BaseModel):
    code: str
    severity: str
    path: str
    message: str


class SiteRead(BaseModel):
    id: UUID
    company_id: UUID
    company_revision: int
    number: int
    language: SiteLanguage
    theme: str
    accent: str | None
    status: SiteStatus
    pages: list[str]
    issues: list[SiteIssue]
    cost_usd: float
    requests: int
    reused_from: UUID | None
    brand_name: str
    domain: str
    stale: bool = Field(description="Карточка изменилась после сборки этой версии.")
    created_at: datetime

    @classmethod
    def from_entity(cls, site: SiteVersion, current_revision: int | None = None) -> SiteRead:
        return cls(
            id=site.id,
            company_id=site.company_id,
            company_revision=site.company_revision,
            number=site.number,
            language=site.language,
            theme=site.theme,
            accent=site.accent,
            status=site.status,
            pages=site.pages,
            issues=[SiteIssue.model_validate(issue) for issue in site.issues],
            cost_usd=site.cost_usd,
            requests=site.requests,
            reused_from=site.reused_from,
            brand_name=site.snapshot["brand"]["name"],
            domain=site.snapshot["brand"]["domain"],
            stale=current_revision is not None and current_revision != site.company_revision,
            created_at=site.created_at,
        )


class ThemeRead(BaseModel):
    key: str
    name: str
    description: str
    accent: str
    background: str
    ink: str
