from typing import Any, Self

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.shared.domain.entities import AggregateRoot
from src.shared.domain.exceptions import InvalidStateError
from src.shared.utils.time import current_datetime

from .enums import JobKind, JobStatus


@dataclass(kw_only=True)
class JobError:
    code: str
    message: str
    details: dict | list = field(default_factory=dict)


@dataclass(kw_only=True)
class Job(AggregateRoot):
    """
    Фоновая операция генерации. Хранит план этапов, текущий этап и расходы, чтобы
    панель показывала прогресс, а после перезапуска было видно, чем всё кончилось.
    """

    kind: JobKind
    status: JobStatus = JobStatus.QUEUED
    stages: list[str] = field(default_factory=list)
    stage_index: int = -1
    message: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    subject_id: UUID | None = None
    result_id: UUID | None = None
    cost_usd: float = 0.0
    budget_usd: float = 0.0
    requests: int = 0
    error: JobError | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        kind: JobKind,
        stages: list[str],
        params: dict[str, Any],
        budget_usd: float,
        subject_id: UUID | None = None,
    ) -> Self:
        if not stages:
            raise ValueError("Job must have at least one stage")
        return cls(
            kind=kind,
            stages=list(stages),
            params=params,
            budget_usd=budget_usd,
            subject_id=subject_id,
        )

    @property
    def stage(self) -> str | None:
        return self.stages[self.stage_index] if 0 <= self.stage_index < len(self.stages) else None

    @property
    def progress(self) -> float:
        if self.status is JobStatus.SUCCEEDED:
            return 1.0
        if self.stage_index < 0:
            return 0.0
        return round(self.stage_index / len(self.stages), 3)

    def _ensure_active(self) -> None:
        if self.status.is_finished:
            raise InvalidStateError(f"Задача уже завершена со статусом {self.status}")

    def start(self) -> None:
        self._ensure_active()
        self.status = JobStatus.RUNNING
        self.started_at = current_datetime()
        self.touch()

    def advance(self, stage: str, message: str = "") -> None:
        """Переходит к этапу плана. Этапы идут только вперёд."""

        self._ensure_active()
        if stage not in self.stages:
            raise ValueError(f"Unknown stage {stage!r}")

        index = self.stages.index(stage)
        if index < self.stage_index:
            raise ValueError(f"Stage {stage!r} is behind the current one")

        self.status = JobStatus.RUNNING
        self.stage_index = index
        self.message = message
        self.touch()

    def report(self, *, message: str | None = None, cost_usd: float, requests: int) -> None:
        if message is not None:
            self.message = message
        self.cost_usd = round(cost_usd, 6)
        self.requests = requests
        self.touch()

    def succeed(self, result_id: UUID | None = None) -> None:
        self._ensure_active()
        self.status = JobStatus.SUCCEEDED
        self.result_id = result_id
        self.message = "Готово"
        self.finished_at = current_datetime()
        self.touch()

    def fail(self, error: JobError) -> None:
        self._ensure_active()
        self.status = JobStatus.FAILED
        self.error = error
        self.finished_at = current_datetime()
        self.touch()
