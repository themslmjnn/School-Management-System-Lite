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
from src.groups import router as group_system_admin_router
from src.subjects import router as subject_system_admin_router
from src.users.routers import guardian as user_guardian_router
from src.users.routers import shared as users_shared_router
from src.users.routers.system_admin import guardian_link as user_guardian_link_router
from src.users.routers.system_admin import users as user_system_admin_router
from src.utils import exceptions as exc
from src.workers.deletion_worker import start_deletion_worker
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
        logger.warning(
            "redis_unavailable",
            error=str(e),
        )

    email_task = asyncio.create_task(run_email_worker())
    deletion_task = asyncio.create_task(start_deletion_worker())

    logger.info("email_task_started")
    logger.info("deletion_task_started")

    yield

    email_task.cancel()
    deletion_task.cancel()

    results = await asyncio.gather(email_task, deletion_task, return_exceptions=True)

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
    title="Student Grade Manager",
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
app.include_router(users_shared_router.router)
app.include_router(user_system_admin_router.router)
app.include_router(user_guardian_router.router)
app.include_router(user_guardian_link_router.router)
app.include_router(subject_system_admin_router.router)
app.include_router(group_system_admin_router.router)

EXCEPTION_STATUS_MAP = {
    exc.EmptyCredentialsError: 400,
    exc.InvalidCredentialsError: 401,
    exc.InvalidAccessTokenError: 401,
    exc.InvalidRefreshTokenError: 401,
    exc.ExpiredRefreshTokenError: 401,
    exc.AccountInactiveError: 409,
    exc.AccountLockedError: 403,
    exc.AccessDeniedError: 403,
    exc.InvalidInviteTokenError: 400,
    exc.ExpiredInviteTokenError: 400,
    exc.InvalidResetPasswordTokenError: 400,
    exc.ExpiredResetPasswordTokenError: 400,
    exc.UserNotFoundError: 404,
    exc.UsernameAlreadyTakenError: 409,
    exc.DuplicateEmailError: 409,
    exc.DuplicatePhoneNumberError: 409,
    exc.PendingEmailNotFoundError: 404,
    exc.NoChangesDetectedError: 409,
    exc.UserAlreadyInactiveError: 409,
    exc.UserAlreadyActiveError: 409,
    exc.UserAlreadyPendingDeletionError: 409,
    exc.MaxStudentsPerEmailError: 409,
    exc.MaxStudentsPerPhoneNumberError: 409,
    exc.MaxStaffOrGuardianPerEmailError: 409,
    exc.MaxStaffOrGuardianPerPhoneNumberError: 409,
    exc.UserTypeMismatchError: 400,
    exc.UserNotPendingActivationError: 404,
    exc.ProfileFieldsNotEditableForRoleError: 403,
    exc.NoPendingEmailChangeError: 404,
    exc.EmailChangeCodeExpiredError: 400,
    exc.InvalidEmailChangeCodeError: 400,
    exc.IncorrectPasswordError: 400,
    exc.CannotCreateDirectorError: 403,
    exc.CannotCreateSystemAdminError: 403,
    exc.GuardianSlotAlreadyFilledError: 409,
    exc.GuardianLinkAlreadyExistsError: 409,
    exc.DuplicateEmailChangeRequestError: 409,
    exc.InvalidGuardianLinkError: 400,
    exc.GuardianLinkNotFoundError: 404,
    exc.StudentSubjectEnrollmentNotFoundError: 404,
    exc.StudentNotFoundError: 404,
    exc.SubjectIsArchivedError: 409,
    exc.StudentNotInGroupError: 404,
    exc.StudentAlreadyEnrolledError: 409,
    exc.TeacherAlreadyHeadOfClassForGroupError: 409,
    exc.HeadOfClassSlotAlreadyFilledError: 409,
    exc.TeachingAssignmentAlreadyExistsError: 409,
    exc.GroupCapacityExceededError: 409,
    exc.GroupArchiveBlockedError: 409,
    exc.SubjectArchiveBlockedError: 403,
    exc.GroupNotArchivedError: 409,
    exc.GroupAlreadyArchivedError: 409,
    exc.SubjectNotArchivedError: 409,
    exc.SubjectAlreadyArchivedError: 409,
    exc.GroupNameYearAlreadyExistsError: 409,
    exc.SubjectCodeAlreadyExistsError: 409,
    exc.GroupNotFoundError: 404,
    exc.SubjectNotFoundError: 404,
    exc.SubjectIsNotArchivedError: 409,
    exc.GroupIsNotArchivedError: 409,
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
        error_type=type(exc).__name__,
        path=request.url.path,
        exc_info=exc,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"},
    )
