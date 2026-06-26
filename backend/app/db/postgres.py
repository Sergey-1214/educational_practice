import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


engine = create_async_engine(
    settings.sqlalchemy_database_url,
    echo=settings.postgres_echo,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def create_tables(max_attempts: int = 30, delay_seconds: int = 2) -> None:
    import app.modules.auth.models  # noqa: F401
    import app.modules.documents.models  # noqa: F401
    import app.modules.history.models  # noqa: F401

    for attempt in range(1, max_attempts + 1):
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            return
        except Exception:
            if attempt == max_attempts:
                raise
            await asyncio.sleep(delay_seconds)
