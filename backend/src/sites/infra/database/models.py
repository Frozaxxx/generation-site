from typing import Any

from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SiteVersionOrm(Base):
    __tablename__ = "site_versions"

    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    company_revision: Mapped[int] = mapped_column(nullable=False)
    number: Mapped[int] = mapped_column(nullable=False)
    language: Mapped[str] = mapped_column(String(4), nullable=False)
    theme: Mapped[str] = mapped_column(String(32), nullable=False)
    accent: Mapped[str | None] = mapped_column(String(7), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    issues: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    pages: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    cost_usd: Mapped[float] = mapped_column(nullable=False, default=0.0)
    requests: Mapped[int] = mapped_column(nullable=False, default=0)
    reused_from: Mapped[UUID | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "number", name="uq_site_versions_company_number"),
        Index("ix_site_versions_company_id", "company_id"),
    )
