from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_system_admin,
)
from src.core.limiter import user_limiter
from src.users.schemas.users import (
    CreateRequest,
    UpdateUser,
    UserResponseAdminDetailed,
)
from src.users.services.system_admin import UserServiceAdmin

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
