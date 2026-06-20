import asyncio

import redis.asyncio as redis
from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import async_db_dependency

router = APIRouter(
    prefix="/health",
    tags=["health"],
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
        return {
            "status": "error",
            "detail": "timed out",
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
        }


async def check_redis(redis_client: redis.Redis) -> dict:
    try:
        async with asyncio.timeout(2.0):
            pong = await redis_client.ping()
        return {"status": "ok" if pong else "error"}
    except TimeoutError:
        return {
            "status": "error",
            "detail": "timed out",
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
        }


@router.get("/ready")
async def readiness(
    request: Request,
    response: Response,
    db: async_db_dependency,
):
    redis_client = request.app.state.redis_client

    pg_result, redis_result = await asyncio.gather(
        check_postgres(db),
        check_redis(redis_client),
        return_exceptions=True,
    )

    checks = {
        "postgres": pg_result
        if not isinstance(pg_result, Exception)
        else {"status": "error", "detail": str(pg_result)},
        "redis": redis_result
        if not isinstance(redis_result, Exception)
        else {"status": "error", "detail": str(redis_result)},
    }

    critical_ok = checks["postgres"]["status"] == "ok"
    overall_ok = critical_ok and checks["redis"]["status"] == "ok"

    if not critical_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    if overall_ok:
        health_status = "ok"
    elif critical_ok:
        health_status = "degraded"
    else:
        health_status = "down"

    return {
        "status": health_status,
        "checks": checks,
    }
