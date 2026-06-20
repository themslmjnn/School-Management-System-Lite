from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.logging import get_logger, setup_logging
from routers import user_admin
from src.utils import custom_exceptions as exc

setup_logging()

logger = get_logger(__name__)

app = FastAPI()


# app.include_router(auth_router.router)
app.include_router(user_admin.router)
# app.include_router(student_routers.router)
# app.include_router(teacher_routers.router)
# app.include_router(subject_routers.router)
# app.include_router(group_routers.router)
# app.include_router(mark_routers.router)

EXCEPTION_STATUS_MAP = {
    exc.CannotCreateSystemAdminError: 403,
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