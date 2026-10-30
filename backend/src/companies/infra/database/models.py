from typing import Any

from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class CompanyOrm(Base):
    __tablename__ = "companies"

    brand_name: Mapped[str] = mapped_column(String(80), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    direction: Mapped[str] = mapped_column(String(64), nullable=False)
    service_type: Mapped[str] = mapped_column(String(64), nullable=False)
    scale: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    revision: Mapped[int] = mapped_column(nullable=False, default=1)

    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    profile: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_companies_status_created_at", "status", "created_at"),)
