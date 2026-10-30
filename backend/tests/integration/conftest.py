import asyncio
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from src.core.database import engine
from src.core.migrations import upgrade_database


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    await asyncio.to_thread(upgrade_database)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    await engine.dispose()
