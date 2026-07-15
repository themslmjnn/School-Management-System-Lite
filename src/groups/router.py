from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    pagination_dependency,
    require_system_admin,
)
from src.groups.schemas import (
    GroupCreate,
    GroupResponse,
    GroupUpdate,
)
from src.groups.service import GroupService
from src.pagination import PaginatedResponse
from src.users.schemas.users import UserResponseAdmin
from src.utils.enums import OrderBy

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    request: GroupCreate,
):
    return await GroupService.create_group(db, current_user.id, request)

@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
    request: GroupUpdate,
):
    return await GroupService.update_group(db, current_user.id, group_id, request)