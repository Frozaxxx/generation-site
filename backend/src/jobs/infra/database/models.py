from typing import Any

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class JobOrm(Base):
    __tablename__ = "jobs"

    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    stages: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    stage_index: Mapped[int] = mapped_column(nullable=False, default=-1)
    message: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    subject_id: Mapped[UUID | None] = mapped_column(nullable=True)
    result_id: Mapped[UUID | None] = mapped_column(nullable=True)
    cost_usd: Mapped[float] = mapped_column(nullable=False, default=0.0)
    budget_usd: Mapped[float] = mapped_column(nullable=False, default=0.0)
    requests: Mapped[int] = mapped_column(nullable=False, default=0)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_subject_id", "subject_id"),
    )
