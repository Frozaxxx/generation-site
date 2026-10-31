import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.jobs.dependencies import job_runner
from src.llm.dependencies import get_openrouter_client

from .logging import configure_logging
from .migrations import upgrade_database
from .settings import storage_config


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging(log_level="INFO")

    for directory in (storage_config.data_dir, storage_config.media_dir, storage_config.sites_dir):
        directory.mkdir(parents=True, exist_ok=True)

    await asyncio.to_thread(upgrade_database)
    await job_runner.recover()

    yield

    await job_runner.shutdown()
    await get_openrouter_client().aclose()


__all__ = ["lifespan"]
