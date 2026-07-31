from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    current_user_dependency,
    require_guardians,
    require_system_admin_and_guardian,
)
from src.core.limiter import user_limiter
from src.users.schemas.guardian_link import ChildResponse
from src.users.schemas.user import (
    ConfirmEmailChange,
    UpdateMeCredentials,
    UpdateMePassword,
    UpdateMeProfile,
    UserResponseSelf,
)
from src.users.services.shared import GuardianLinkServiceShared, UserServiceSelf

router = APIRouter(
    prefix="/users",
    tags=["Users - Shared"],
)


@router.patch(
    "/me/profile",
    response_model=UserResponseSelf,
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("10/minute")
async def update_me_profile(
    request: Request,
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin_and_guardian)],
    update_request: UpdateMeProfile,
):
    return await UserServiceSelf.update_me_profile(db, current_user.id, update_request)


@router.patch(
    "/me/credentials",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("10/minute")
async def update_me_credentials(
    request: Request,
    db: async_db_dependency,
    current_user: current_user_dependency,
    update_request: UpdateMeCredentials,
):
    await UserServiceSelf.update_me_credentials(db, current_user.id, update_request)


@router.post(
    "/me/credentials/confirm-email",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("5/minute")
async def confirm_email_change(
    request: Request,
    db: async_db_dependency,
    current_user: current_user_dependency,
    confirm_request: ConfirmEmailChange,
):
    await UserServiceSelf.confirm_email_change(db, current_user.id, confirm_request)


@router.patch(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("10/minute")
async def update_me_password(
    request: Request,
    db: async_db_dependency,
    current_user: current_user_dependency,
    update_request: UpdateMePassword,
):
    await UserServiceSelf.update_me_password(db, current_user.id, update_request)


@router.get("/me/children", response_model=list[ChildResponse])
async def get_my_children(
    db: async_db_dependency,
    current_user: Annotated[
        CurrentUser,
        Depends(require_guardians),
    ],
):
    return await GuardianLinkServiceShared.get_children_for_guardian(
        db, current_user.id
    )
