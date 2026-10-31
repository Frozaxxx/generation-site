import pytest

from src.jobs.domain.entities import Job, JobError
from src.jobs.domain.enums import JobKind, JobStatus
from src.shared.domain.exceptions import InvalidStateError


def make_job() -> Job:
    return Job.create(kind=JobKind.COMPANY, stages=["a", "b", "c", "d"], params={}, budget_usd=1)


def test_progress_follows_stages():
    job = make_job()
    job.start()
    job.advance("c", "работаю")

    assert job.stage == "c"
    assert job.progress == 0.5

    job.succeed()
    assert job.progress == 1.0


def test_stages_only_go_forward():
    job = make_job()
    job.advance("b")

    with pytest.raises(ValueError, match="behind"):
        job.advance("a")


def test_finished_job_is_immutable():
    job = make_job()
    job.fail(JobError(code="X", message="ошибка"))

    assert job.status is JobStatus.FAILED
    with pytest.raises(InvalidStateError):
        job.advance("b")
