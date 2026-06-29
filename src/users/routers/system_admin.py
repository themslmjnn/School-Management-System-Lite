from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status

from pagination import PaginatedResponse
from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_system_admin,
    pagination_dependency,
)
from src.core.limiter import user_limiter
from src.users.schemas.users import (
    CreateStaffAdmin,
    CreateStudentAdmin,
    UserResponseAdmin,
    UserResponseAdminDetailed,
)
from src.users.services.users import UserServiceAdmin

router = APIRouter(
    prefix="/users",
    tags=["Users - System Admin"],
)


@router.post(
    "/staff",
    response_model=UserResponseAdminDetailed,
    status_code=status.HTTP_201_CREATED,
)
@user_limiter.limit("10/minute")
async def create_staff(
    request: Request,
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: CreateStaffAdmin,
):
    return await UserServiceAdmin.create_staff(db, current_user.id, create_request)


@router.post(
    "/student",
    response_model=UserResponseAdminDetailed,
    status_code=status.HTTP_201_CREATED,
)
@user_limiter.limit("10/minute")
async def create_student(
    request: Request,
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: CreateStudentAdmin,
):
    return await UserServiceAdmin.create_student(db, current_user.id, create_request)


# @router.get("/staff")
# async def get_staff(): ...


# @router.get("/students")
# async def get_students(): ...


# @router.get("/{user_id}")
# async def get_user(): ...


@router.delete("/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
@user_limiter.limit("10/minute")
async def delete_parent(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    target_user_id: Annotated[int, Path(ge=1)],
): 
    return UserServiceAdmin.delete_parent(db, current_user.id, target_user_id)


# @router.patch("/{user_id}/deactivate")
# async def deactivate_user(): ...


# @router.patch("/{user_id}/activate")
# async def activate_user(): ...


# @router.patch("/{user_id}")
# async def update_user(): ...


# @router.post("/{user_id}/reset_password_request")
# async def create_reset_password_request(): ...
