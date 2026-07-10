from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_system_admin,
)
from src.core.limiter import user_limiter
from src.users.schemas.users import (
    CreateRequest,
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
