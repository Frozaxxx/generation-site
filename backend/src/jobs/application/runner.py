"""
Фоновое выполнение генераций внутри процесса сервера.

Для тестового задания этого достаточно: задачи короткие (минуты), состояние и
расходы сохраняются в базе после каждого этапа. Для продакшена обработчик можно
вынести в taskiq-воркер, не меняя `JobContext` и обработчики.
"""

from typing import Any

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.llm.domain.budget import OperationBudget
from src.shared.domain.exceptions import DomainError, NotFoundError

from ..domain.entities import Job, JobError
from ..domain.enums import JobKind
from ..infra.database.repos.jobs import SqlJobRepository

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]
JobHandler = Callable[["JobContext"], Awaitable[UUID | None]]

INTERRUPTED_MESSAGE = "Задача прервана перезапуском сервера, запустите генерацию снова"


class JobContext:
    """То, что видит обработчик: параметры, бюджет и отметка этапов."""

    def __init__(
        self,
        *,
        job_id: UUID,
        params: dict[str, Any],
        budget: OperationBudget,
        session_factory: SessionFactory,
    ) -> None:
        self.job_id = job_id
        self.params = params
        self.budget = budget
        self._session_factory = session_factory

    async def stage(self, name: str, message: str = "") -> None:
        """Отмечает начало этапа и сохраняет текущие расходы."""

        def apply(job: Job) -> None:
            job.advance(name, message)
            job.report(cost_usd=self.budget.spent_usd, requests=self.budget.requests)

        await self.update(apply)

    async def note(self, message: str) -> None:
        """Уточняет текущий этап, например «фото 3 из 6»."""

        await self.update(
            lambda job: job.report(
                message=message, cost_usd=self.budget.spent_usd, requests=self.budget.requests
            )
        )

    async def update(self, apply: Callable[[Job], None]) -> None:
        async with self._session_factory() as session:
            repo = SqlJobRepository(session)
            job = await repo.read(self.job_id)
            if job is None:
                raise NotFoundError(f"Задача {self.job_id} не найдена")
            apply(job)
            await repo.upsert(job)
            await session.commit()


class JobRunner:
    def __init__(self, session_factory: SessionFactory, *, max_concurrent: int = 2) -> None:
        self._session_factory = session_factory
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._tasks: set[asyncio.Task[None]] = set()

    async def submit(
        self,
        *,
        kind: JobKind,
        stages: list[str],
        params: dict[str, Any],
        handler: JobHandler,
        budget: OperationBudget,
        subject_id: UUID | None = None,
    ) -> Job:
        """Сохраняет задачу и запускает её в фоне. Возвращается сразу."""

        job = Job.create(
            kind=kind,
            stages=stages,
            params=params,
            budget_usd=budget.limit_usd,
            subject_id=subject_id,
        )
        async with self._session_factory() as session:
            await SqlJobRepository(session).create(job)
            await session.commit()

        context = JobContext(
            job_id=job.id,
            params=params,
            budget=budget,
            session_factory=self._session_factory,
        )
        task = asyncio.create_task(self._run(job.id, handler, context), name=f"job-{job.id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return job

    async def wait_all(self) -> None:
        """Для тестов и CLI: дождаться завершения запущенных задач."""

        while self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    async def recover(self) -> int:
        """При старте сервера помечает незавершённые задачи прерванными."""

        async with self._session_factory() as session:
            count = await SqlJobRepository(session).fail_unfinished(INTERRUPTED_MESSAGE)
            await session.commit()
        return count

    async def shutdown(self) -> None:
        for task in list(self._tasks):
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        # Задачи, отменённые до старта, не успели записать итог.
        await self.recover()

    async def _run(self, job_id: UUID, handler: JobHandler, context: JobContext) -> None:
        async with self._semaphore:
            await self._save(context, lambda job: job.start())
            try:
                result_id = await handler(context)
            except asyncio.CancelledError:
                await self._fail(context, JobError(code="CANCELLED", message=INTERRUPTED_MESSAGE))
                raise
            except DomainError as error:
                logger.warning(
                    "Job failed",
                    extra={"job_id": str(job_id), "code": error.error_code},
                )
                await self._fail(
                    context,
                    JobError(code=error.error_code, message=error.message, details=error.details),
                )
            except Exception:
                logger.exception("Job crashed", extra={"job_id": str(job_id)})
                await self._fail(
                    context,
                    JobError(
                        code="INTERNAL_ERROR",
                        message="Внутренняя ошибка, подробности в логах сервера",
                    ),
                )
            else:
                await self._save(context, lambda job: job.succeed(result_id))

    async def _fail(self, context: JobContext, error: JobError) -> None:
        await self._save(context, lambda job: job.fail(error))

    @staticmethod
    async def _save(context: JobContext, apply: Callable[[Job], None]) -> None:
        def wrapped(job: Job) -> None:
            job.report(cost_usd=context.budget.spent_usd, requests=context.budget.requests)
            apply(job)

        # Сохранение итога не должно прерываться отменой задачи.
        await asyncio.shield(context.update(wrapped))
