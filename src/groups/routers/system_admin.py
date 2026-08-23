from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    pagination_dependency,
    require_system_admin,
)
from src.core.pagination import PaginatedResponse
from src.groups.schemas import (
    CreateGroupAdmin,
    GroupResponseAdminDetailed,
    GroupResponseBase,
    SearchGroupAdmin,
    UpdateGroupAdmin,
)
from src.groups.services.system_admin import GroupServiceAdmin
from src.utils.enums import GroupSortField, OrderBy

router = APIRouter(
    prefix="/groups",
    tags=["Groups - System Admin"],
)


@router.post(
    "", response_model=GroupResponseAdminDetailed, status_code=status.HTTP_201_CREATED
)
async def create_group(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: CreateGroupAdmin,
):
    return await GroupServiceAdmin.create_group(
        session, current_user.id, create_request
    )


@router.patch("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_group(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
    update_request: UpdateGroupAdmin,
):
    await GroupServiceAdmin.update_group(
        session, current_user.id, group_id, update_request
    )


@router.patch("/{group_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_group(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
):
    await GroupServiceAdmin.archive_group(session, current_user.id, group_id)


@router.patch("/{group_id}/restoration", status_code=status.HTTP_204_NO_CONTENT)
async def restore_group(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
):
    await GroupServiceAdmin.restore_group(session, current_user.id, group_id)


@router.get(
    "",
    response_model=PaginatedResponse[GroupResponseBase],
    status_code=status.HTTP_200_OK,
)
async def get_groups(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    pagination: pagination_dependency,
    filters: Annotated[SearchGroupAdmin, Depends()],
    sort_by: str = GroupSortField.ACADEMIC_YEAR,
    order: str = OrderBy.DESC,
):
    return await GroupServiceAdmin.get_groups(
        session,
        pagination.skip,
        pagination.limit,
        filters,
        sort_by,
        order,
    )


@router.get(
    "/{group_id}",
    response_model=GroupResponseAdminDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_group_by_id(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
):
    return await GroupServiceAdmin.get_group_by_id(session, group_id)
