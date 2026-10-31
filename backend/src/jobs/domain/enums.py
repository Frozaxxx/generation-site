from enum import StrEnum, auto


class JobKind(StrEnum):
    COMPANY = auto()
    SITE = auto()


class JobStatus(StrEnum):
    QUEUED = auto()
    RUNNING = auto()
    SUCCEEDED = auto()
    FAILED = auto()

    @property
    def is_finished(self) -> bool:
        return self in {JobStatus.SUCCEEDED, JobStatus.FAILED}
