import asyncio

import redis.asyncio as redis
from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import async_session_dependency
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/live")
async def liveness():
    return {"status": "ok"}


async def check_postgres(session: AsyncSession) -> dict:
    try:
        async with asyncio.timeout(2.0):
            await session.execute(text("SELECT 1"))

        return {"status": "ok"}

    except TimeoutError:
        logger.warning("health_check_postgres_timeout")

        return {
            "status": "error",
            "detail": "timed out",
        }

    except Exception as exc:
        logger.warning(
            "health_check_postgres_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )

        return {
            "status": "error",
            "detail": "unavailable",
        }


async def check_redis(redis_client: redis.Redis) -> dict:
    try:
        async with asyncio.timeout(2.0):
            pong = await redis_client.ping()

        return {"status": "ok" if pong else "error"}

    except TimeoutError:
        logger.warning("health_check_redis_timeout")

        return {
            "status": "error",
            "detail": "timed out",
        }

    except Exception as exc:
        logger.warning(
            "health_check_redis_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )

        return {
            "status": "error",
            "detail": "unavailable",
        }


@router.get("/ready")
async def readiness(
    request: Request,
    response: Response,
    session: async_session_dependency,
):
    redis_client = request.app.state.redis_client

    pg_result, redis_result = await asyncio.gather(
        check_postgres(session),
        check_redis(redis_client),
        return_exceptions=True,
    )

    postgres_check = {
        "postgres": pg_result
        if not isinstance(pg_result, Exception)
        else {"status": "error", "detail": "unavailable"}
    }
    redis_check = {
        "redis": redis_result
        if not isinstance(redis_result, Exception)
        else {"status": "error", "detail": "unavailable"}
    }

    if isinstance(pg_result, Exception):
        logger.error(
            "health_check_postgres_unhandled",
            error=str(pg_result),
            error_type=type(pg_result).__name__,
        )

    if isinstance(redis_result, Exception):
        logger.error(
            "health_check_redis_unhandled",
            error=str(redis_result),
            error_type=type(redis_result).__name__,
        )

    critical_ok = postgres_check["status"] == "ok" and redis_check["status"] == "ok"

    if not critical_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    health_status = "ok" if critical_ok else "down"

    return {
        "status": health_status,
        "postgres_check": postgres_check,
        "redis_check": redis_check,
    }
