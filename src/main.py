from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from src.api.health import router as health_router
from src.core.caching import redis_client
from src.core.config import settings
from src.core.limiter import ip_limiter
from src.core.logging import get_logger, setup_logging
from src.users.routers import system_admin as user_system_admin_router
from src.utils import exceptions as exc

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

app.state.limiter = ip_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(health_router)
app.include_router(user_system_admin_router.router)

EXCEPTION_STATUS_MAP = {
    exc.AccessDeniedError: 403,
    exc.AccountInactiveError: 409,
    exc.CannotCreateDirectorError: 403,
    exc.CannotCreateSystemAdminError: 403,
    exc.EmptyCredentialsError: 400,
    exc.InvalidAccessTokenError: 401,
    exc.ExpiredRefreshTokenError: 401,
    exc.InvalidRefreshTokenError: 401,
}

@app.exception_handler(exc.AppException)
async def app_exception_handler(
    request: Request, exc: exc.AppException
) -> JSONResponse:
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)

    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred"},
    )