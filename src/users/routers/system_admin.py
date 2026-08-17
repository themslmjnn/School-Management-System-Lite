from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    pagination_dependency,
    require_system_admin,
)
from src.core.limiter import user_limiter
from src.core.pagination import PaginatedResponse
from src.users.schemas.system_admin import (
    CreateUserRequest,
    SearchUserAdmin,
    StudentResponseAdmin,
    StudentResponseAdminDetailed,
    UpdateUserRequest,
    UserResponseAdmin,
    UserResponseAdminDetailed,
)
from src.users.services.system_admin import UserServiceAdmin
from src.users.utils.user_credentials_schema import UpdateUserCredentials
from src.utils.enums import OrderBy, UserSortField

router = APIRouter(
    prefix="/users",
    tags=["Users - System Admin"],
)


@router.post(
    "",
    response_model=UserResponseAdminDetailed,
    status_code=status.HTTP_201_CREATED,
)
@user_limiter.limit("10/minute")
async def register_user(
    request: Request,
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: CreateUserRequest,
):
    return await UserServiceAdmin.register_user(
        session, current_user.id, create_request
    )


@router.patch(
    "/{target_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("10/minute")
async def update_user(
    request: Request,
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
    update_request: UpdateUserRequest,
):
    await UserServiceAdmin.update_user(
        session, current_user.id, target_user_id, update_request
    )


@router.patch(
    "/{target_user_id}/credentials",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("5/minute")
async def update_user_credentials(
    request: Request,
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
    update_request: UpdateUserCredentials,
):
    await UserServiceAdmin.update_user_credentials(
        session, current_user.id, target_user_id, update_request
    )


@router.patch("/{target_user_id}/deactivation", status_code=status.HTTP_204_NO_CONTENT)
@user_limiter.limit("10/minute")
async def deactivate_user(
    request: Request,
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    await UserServiceAdmin.deactivate_user(session, current_user.id, target_user_id)


@router.patch("/{target_user_id}/activation", status_code=status.HTTP_204_NO_CONTENT)
@user_limiter.limit("10/minute")
async def activate_user(
    request: Request,
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    await UserServiceAdmin.activate_user(session, current_user.id, target_user_id)


@router.post("/{target_user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
@user_limiter.limit("5/minute")
async def create_reset_password_request(
    request: Request,
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    await UserServiceAdmin.create_reset_password_request(
        session, current_user.id, target_user_id
    )


@router.post(
    "/{target_user_id}/resend-invite",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_limiter.limit("5/minute")
async def resend_activation_invite(
    request: Request,
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
):
    await UserServiceAdmin.resend_activation_invite(
        session, current_user.id, target_user_id
    )


@router.get(
    "/teachers",
    response_model=PaginatedResponse[UserResponseAdmin],
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("15/minute")
async def get_teachers(
    request: Request,
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    pagination: pagination_dependency,
    filters: Annotated[SearchUserAdmin, Depends()],
    sort_by: str = UserSortField.CREATED_AT,
    order: str = OrderBy.DESC,
):
    return await UserServiceAdmin.get_teachers(
        session,
        pagination.skip,
        pagination.limit,
        filters,
        sort_by,
        order,
    )


@router.get(
    "/teachers/{target_teacher_id}",
    response_model=UserResponseAdminDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_staff_by_id(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    target_staff_id: Annotated[int, Path(ge=1)],
):
    return await UserServiceAdmin.get_teacher_by_id(session, target_staff_id)


@router.get(
    "/students",
    response_model=PaginatedResponse[StudentResponseAdmin],
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("15/minute")
async def get_students(
    request: Request,
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    pagination: pagination_dependency,
    filters: Annotated[SearchUserAdmin, Depends()],
    group_id: int | None = None,
    sort_by: str = UserSortField.CREATED_AT,
    order: str = OrderBy.DESC,
):
    return await UserServiceAdmin.get_students(
        session, pagination.skip, pagination.limit, group_id, filters, sort_by, order
    )


@router.get(
    "/students/{target_student_id}",
    response_model=StudentResponseAdminDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_student_by_id(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    target_student_id: Annotated[int, Path(ge=1)],
):
    return await UserServiceAdmin.get_student_by_id(session, target_student_id)
