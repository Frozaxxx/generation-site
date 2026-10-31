from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import database_config

engine = create_async_engine(
    url=database_config.url,
    echo=database_config.echo,
    hide_parameters=True,
    # Фоновые задачи пишут прогресс параллельно с запросами панели.
    connect_args={"timeout": 30} if database_config.url.startswith("sqlite") else {},
)


@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """SQLite по умолчанию не проверяет внешние ключи."""

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


sessionmaker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def session_factory() -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        yield session


async def get_db() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
