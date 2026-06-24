import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.db.postgres import Base, engine


async def init_db(max_attempts: int = 10, delay_seconds: int = 2) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            return
        except OSError:
            if attempt == max_attempts:
                raise
            await asyncio.sleep(delay_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    from app.modules.auth import models as auth_models  # noqa: F401

    await init_db()

    yield


app = FastAPI(
    title="Educational Practice API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
