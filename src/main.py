from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.health import router as health_router
from src.core.caching import redis_client
from src.core.config import settings
from src.core.logging import get_logger, setup_logging

setup_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_client = redis_client

    try:
        await redis_client.ping()

        logger.info("redis_connected")
    except Exception as e:
        logger.warning(
            "redis_unavailable",
            error=str(e),
        )

    yield

    await redis_client.aclose()

    logger.info("redis_disconnected")


app = FastAPI(
    title="Student Grade Manager",
    lifespan=lifespan,
    docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
)

app.include_router(health_router)
