from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_system_admin,
)
from src.users.schemas import (
    CreateUserAdmin,
    UserResponseAdminDetailed,
)
from src.users.service import UserServiceAdmin

router = APIRouter(
    prefix="/users",
    tags=["Users - System Admin"],
)


@router.post(
    "", response_model=UserResponseAdminDetailed, status_code=status.HTTP_201_CREATED
)
async def create_user(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: CreateUserAdmin,
):
    return UserServiceAdmin.create_user(db, current_user.id, create_request)


@router.get("")
async def get_users(): ...


@router.patch("/{user_id}")
async def get_user(): ...


@router.delete("/{user_id}")
async def delete_user(): ...


@router.patch("/{user_id}/deactivate")
async def deactivate_user(): ...


@router.patch("/{user_id}/activate")
async def activate_user(): ...


@router.patch("/{user_id}")
async def update_user(): ...


@router.post("/{user_id}/reset_password_request")
async def create_reset_password_request(): ...
