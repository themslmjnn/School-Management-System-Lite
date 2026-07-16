import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.orm import configure_mappers

import src.models  # noqa: F401
from src.academics.exceptions import exceptions as academic_exc
from src.api.health import router as health_router
from src.auth.router import router as auth_router
from src.core.caching import redis_client
from src.core.config import settings
from src.core.limiter import ip_limiter
from src.core.logging import get_logger, setup_logging
from src.core.middleware import RequestIDMiddleware
from src.emails.exceptions import exceptions as email_exc
from src.groups import router as group_system_admin_router
from src.groups.exceptions import exceptions as groups_exc
from src.subjects import router as subject_system_admin_router
from src.subjects.exceptions import exceptions as subject_exc
from src.users.exceptions import exceptions as user_exc
from src.users.routers import guardian as user_guardian_router
from src.users.routers import shared as users_shared_router
from src.users.routers.system_admin import guardian_link as user_guardian_link_router
from src.users.routers.system_admin import user as user_system_admin_router
from src.utils import base_exception as base_exc
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
    base_exc.EmptyCredentialsError: 400,
    base_exc.InvalidCredentialsError: 401,
    base_exc.InvalidAccessTokenError: 401,
    base_exc.InvalidRefreshTokenError: 401,
    base_exc.ExpiredRefreshTokenError: 401,
    base_exc.AccountInactiveError: 409,
    base_exc.AccountLockedError: 403,
    base_exc.AccessDeniedError: 403,
    base_exc.InvalidInviteTokenError: 400,
    base_exc.ExpiredInviteTokenError: 400,
    base_exc.InvalidResetPasswordTokenError: 400,
    base_exc.ExpiredResetPasswordTokenError: 400,
    user_exc.UserNotFoundError: 404,
    user_exc.UsernameAlreadyTakenError: 409,
    user_exc.DuplicateEmailError: 409,
    user_exc.DuplicatePhoneNumberError: 409,
    email_exc.PendingEmailNotFoundError: 404,
    base_exc.NoChangesDetectedError: 409,
    user_exc.UserAlreadyInactiveError: 409,
    user_exc.UserAlreadyActiveError: 409,
    user_exc.UserAlreadyPendingDeletionError: 409,
    user_exc.MaxStudentsPerEmailError: 409,
    user_exc.MaxStudentsPerPhoneNumberError: 409,
    user_exc.MaxStaffOrGuardianPerEmailError: 409,
    user_exc.MaxStaffOrGuardianPerPhoneNumberError: 409,
    user_exc.UserTypeMismatchError: 400,
    user_exc.UserNotPendingActivationError: 404,
    user_exc.ProfileFieldsNotEditableForRoleError: 403,
    user_exc.NoPendingEmailChangeError: 404,
    user_exc.EmailChangeCodeExpiredError: 400,
    user_exc.InvalidEmailChangeCodeError: 400,
    user_exc.IncorrectPasswordError: 400,
    user_exc.GuardianSlotAlreadyFilledError: 409,
    user_exc.GuardianLinkAlreadyExistsError: 409,
    user_exc.DuplicateEmailChangeRequestError: 409,
    user_exc.InvalidGuardianLinkError: 400,
    user_exc.GuardianLinkNotFoundError: 404,
    academic_exc.StudentSubjectEnrollmentNotFoundError: 404,
    academic_exc.StudentNotFoundError: 404,
    subject_exc.SubjectIsArchivedError: 409,
    academic_exc.StudentNotInGroupError: 404,
    academic_exc.StudentAlreadyEnrolledError: 409,
    academic_exc.TeacherAlreadyHeadOfClassForGroupError: 409,
    academic_exc.HeadOfClassSlotAlreadyFilledError: 409,
    academic_exc.TeachingAssignmentAlreadyExistsError: 409,
    groups_exc.GroupCapacityExceededError: 409,
    groups_exc.GroupArchiveBlockedError: 409,
    subject_exc.SubjectArchiveBlockedError: 403,
    groups_exc.GroupNotArchivedError: 409,
    groups_exc.GroupAlreadyArchivedError: 409,
    subject_exc.SubjectNotArchivedError: 409,
    subject_exc.SubjectAlreadyArchivedError: 409,
    groups_exc.GroupNameYearAlreadyExistsError: 409,
    subject_exc.SubjectCodeAlreadyExistsError: 409,
    groups_exc.GroupNotFoundError: 404,
    subject_exc.SubjectNotFoundError: 404,
    subject_exc.SubjectIsNotArchivedError: 409,
    groups_exc.GroupIsNotArchivedError: 409,
}


@app.exception_handler(base_exc.AppException)
async def app_exception_handler(
    request: Request, exc: base_exc.AppException
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
