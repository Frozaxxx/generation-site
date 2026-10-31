from typing import Annotated

from fastapi import Depends

from src.core.database import session_factory
from src.shared.dependencies.database import DBSession

from ..application.repos import JobRepository
from ..application.runner import JobRunner
from ..infra.database.repos.jobs import SqlJobRepository

job_runner = JobRunner(session_factory)


def get_job_repo(session: DBSession) -> SqlJobRepository:
    return SqlJobRepository(session)


def get_job_runner() -> JobRunner:
    return job_runner


JobRepoDep = Annotated[JobRepository, Depends(get_job_repo)]
JobRunnerDep = Annotated[JobRunner, Depends(get_job_runner)]

__all__ = ["JobRepoDep", "JobRunnerDep", "get_job_runner", "job_runner"]
