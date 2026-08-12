from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    current_user_dependency,
    require_student,
    require_system_admin_and_guardian,
)
from src.core.limiter import user_limiter
from src.users.schemas.shared import (
    ConfirmEmailChange,
    StudentResponseSelf,
    UpdateMeCredentials,
    UpdateMePassword,
    UpdateMeProfile,
    UserResponseSelf,
)
from src.users.services.shared import (
    StudentService,
    UserServiceSelf,
)

router = APIRouter(
    prefix="/users",
    tags=["Users - Shared - User"],
)


@router.get("/me", response_model=UserResponseSelf, status_code=status.HTTP_200_OK)
async def get_my_profile(
    session: async_session_dependency,
    current_user: current_user_dependency,
):
    return await UserServiceSelf.get_my_profile(session, current_user)


@router.patch(
    "/me/profile",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("5/minute")
async def update_me_profile(
    request: Request,
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin_and_guardian)],
    update_request: UpdateMeProfile,
):
    await UserServiceSelf.update_me_profile(session, current_user.id, update_request)


@router.patch(
    "/me/credentials",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("5/minute")
async def update_me_credentials(
    request: Request,
    session: async_session_dependency,
    current_user: current_user_dependency,
    update_request: UpdateMeCredentials,
):
    await UserServiceSelf.update_me_credentials(
        session, current_user.id, update_request
    )


@router.post(
    "/me/credentials/confirm-email",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("5/minute")
async def confirm_email_change(
    request: Request,
    session: async_session_dependency,
    current_user: current_user_dependency,
    confirm_request: ConfirmEmailChange,
):
    await UserServiceSelf.confirm_email_change(
        session, current_user.id, confirm_request
    )


@router.patch(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("5/minute")
async def update_me_password(
    request: Request,
    session: async_session_dependency,
    current_user: current_user_dependency,
    update_request: UpdateMePassword,
):
    await UserServiceSelf.update_me_password(session, current_user.id, update_request)


@router.get(
    "/students/me", response_model=StudentResponseSelf, status_code=status.HTTP_200_OK
)
async def get_my_student_profile(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_student)],
):
    return await StudentService.get_my_profile(session, current_user)
