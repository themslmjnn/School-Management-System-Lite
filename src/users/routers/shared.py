from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    current_user_dependency,
    require_guardians,
    require_system_admin_and_guardian,
)
from src.core.limiter import user_limiter
from src.users.schemas.shared import (
    ConfirmEmailChange,
    UpdateMeCredentials,
    UpdateMePassword,
    UpdateMeProfile,
    UserResponseSelf,
)
from src.users.schemas.system_admin.guardian_link import ChildResponse
from src.users.services.shared import GuardianLinkServiceShared, UserServiceSelf

router = APIRouter(
    prefix="/users",
    tags=["Users - Shared - User"],
)


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


@router.get("/me/children", response_model=list[ChildResponse])
async def get_my_children(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_guardians)],
):
    return await GuardianLinkServiceShared.get_children_for_guardian(
        session, current_user.id
    )
