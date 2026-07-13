from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    pagination_dependency,
    require_system_admin,
)
from src.core.limiter import user_limiter
from src.pagination import PaginatedResponse
from src.users.schemas.users import (
    CreateRequest,
    SearchUserAdmin,
    UpdateUser,
    UpdateUserCredentials,
    UserResponseAdmin,
    UserResponseAdminDetailed,
)
from src.users.services.system_admin import UserServiceAdmin
from src.utils.enums import OrderBy, UserSortField

router = APIRouter(
    prefix="/users",
    tags=["Users - System Admin"],
)


# COMPLETED!!!
@router.post(
    "",
    response_model=UserResponseAdminDetailed,
    status_code=status.HTTP_201_CREATED,
)
@user_limiter.limit("10/minute")
async def register_user(
    request: Request,
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: CreateRequest,
):
    return await UserServiceAdmin.register_user(db, current_user.id, create_request)


@router.patch(
    "/{target_user_id}",
    response_model=UserResponseAdminDetailed,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
    update_request: UpdateUser,
):
    return await UserServiceAdmin.update_user(
        db, current_user.id, target_user_id, update_request
    )


@router.patch(
    "/{target_user_id}/credentials",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_user_credentials(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
    update_request: UpdateUserCredentials,
):
    await UserServiceAdmin.update_user_credentials(
        db, current_user.id, target_user_id, update_request
    )


@router.post(
    "/{target_user_id}/guardian-deletion",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def create_guardian_deletion_request(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: int,
):
    await UserServiceAdmin.create_guardian_deletion_request(
        db, current_user.id, target_user_id
    )


@router.post(
    "/{target_user_id}/cancel-deletion",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_guardian_deletion(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: int,
):
    await UserServiceAdmin.cancel_guardian_deletion_request(
        db, current_user.id, target_user_id
    )


@router.patch("/{target_user_id}/deactivation", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    return await UserServiceAdmin.deactivate_user(db, current_user.id, target_user_id)


@router.patch("/{target_user_id}/activation", status_code=status.HTTP_204_NO_CONTENT)
async def activate_user(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    return await UserServiceAdmin.activate_user(db, current_user.id, target_user_id)


@router.post("/{target_user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
@user_limiter.limit("5/minute")
async def create_reset_password_request(
    request: Request,
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    await UserServiceAdmin.create_reset_password_request(
        db, current_user, target_user_id
    )


@router.post(
    "/{target_user_id}/resend-invite",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def resend_activation_invite(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    await UserServiceAdmin.resend_activation_invite(db, current_user.id, target_user_id)


@router.get(
    "/staff",
    response_model=PaginatedResponse[UserResponseAdmin],
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("15/minute")
async def get_staff(
    request: Request,
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    pagination: pagination_dependency,
    filters: Annotated[SearchUserAdmin, Depends()],
    sort_by: str = UserSortField.CREATED_AT,
    order: str = OrderBy.DESC,
):
    return await UserServiceAdmin.get_staff(
        db,
        pagination.skip,
        pagination.limit,
        filters,
        sort_by,
        order,
    )


@router.get(
    "/staff/{target_user_id}",
    response_model=UserResponseAdminDetailed | dict,
    status_code=status.HTTP_200_OK,
)
async def get_staff_by_id(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    return await UserServiceAdmin.get_staff_by_id(db, target_user_id)


@router.get(
    "/guardians",
    response_model=PaginatedResponse[UserResponseAdmin],
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("15/minute")
async def get_guardians(
    request: Request,
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    pagination: pagination_dependency,
    filters: Annotated[SearchUserAdmin, Depends()],
    sort_by: str = UserSortField.CREATED_AT,
    order: str = OrderBy.DESC,
):
    return await UserServiceAdmin.get_guardians(
        db,
        pagination.skip,
        pagination.limit,
        filters,
        sort_by,
        order,
    )


@router.get(
    "/guardians/{target_user_id}",
    response_model=UserResponseAdminDetailed | dict,
    status_code=status.HTTP_200_OK,
)
async def get_guardian_by_id(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    return await UserServiceAdmin.get_guardian_by_id(db, target_user_id)
