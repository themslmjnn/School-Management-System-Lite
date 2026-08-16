import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.orm import configure_mappers

import src.models  # noqa: F401
from src.api.health import router as health_router
from src.auth.router import router as auth_router
from src.core.caching import redis_client
from src.core.config import settings
from src.core.limiter import ip_limiter
from src.core.logging import get_logger, setup_logging
from src.core.middleware import RequestIDMiddleware
from src.users.routers import shared as user_shared_router
from src.users.routers import system_admin as user_system_admin_router
from src.utils import base_exception as base_exc
from src.workers.email_worker import run_email_worker

configure_mappers()

setup_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_client = redis_client

    try:
        await redis_client.ping()

        logger.info("redis_connected")
    except Exception as e:
        if settings.ENVIRONMENT == "production":
            logger.error(
                "redis_unavailable_startup_aborted",
                error=str(e),
            )

            raise RuntimeError(
                "Redis is required in production and is currently unavailable. "
                "Aborting startup."
            ) from e

        logger.warning(
            "redis_unavailable",
            error=str(e),
            impact="rate_limiting_will_fail_on_rate_limited_endpoints",
        )

    email_task = asyncio.create_task(run_email_worker())

    logger.info("email_task_started")

    yield

    email_task.cancel()

    results = await asyncio.gather(email_task, return_exceptions=True)

    for result in results:
        if isinstance(result, BaseException) and not isinstance(
            result, asyncio.CancelledError
        ):
            logger.error(
                "worker_shutdown_error",
                error=str(result),
                error_type=type(result).__name__,
            )

    await redis_client.aclose()

    logger.info("redis_disconnected")


app = FastAPI(
    title="School Management System — Lite",
    lifespan=lifespan,
    docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
)

app.add_middleware(RequestIDMiddleware)

app.state.limiter = ip_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_shared_router.router)
app.include_router(user_system_admin_router.router)


@app.exception_handler(base_exc.AppException)
async def app_exception_handler(
    request: Request, exc: base_exc.AppException
) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error(
            "app_exception_server_error",
            error=str(exc.detail),
            error_type=type(exc).__name__,
            path=request.url.path,
        )
    else:
        logger.info(
            "app_exception_handled",
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            path=request.url.path,
        )

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        exc_info=exc,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"},
    )
