from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    pagination_dependency,
    require_system_admin,
)
from src.core.pagination import PaginatedResponse
from src.groups.schemas import (
    GroupCreate,
    GroupResponse,
    GroupUpdate,
    SearchGroup,
)
from src.groups.service import GroupService
from src.users.schemas.user import UserResponseAdmin
from src.utils.enums import GroupSortField, OrderBy

router = APIRouter(
    prefix="/groups",
    tags=["Groups - System Admin"],
)


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: GroupCreate,
):
    return await GroupService.create_group(db, current_user.id, create_request)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
    update_request: GroupUpdate,
):
    return await GroupService.update_group(
        db, current_user.id, group_id, update_request
    )


@router.patch("/{group_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_group(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
):
    await GroupService.archive_group(db, current_user.id, group_id)


@router.patch("/{group_id}/restoration", status_code=status.HTTP_204_NO_CONTENT)
async def restore_group(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
):
    await GroupService.restore_group(db, current_user.id, group_id)


@router.get("", response_model=PaginatedResponse[GroupResponse])
async def get_groups(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    pagination: pagination_dependency,
    filters: Annotated[SearchGroup, Depends()],
    sort_by: str = GroupSortField.ACADEMIC_YEAR,
    order: str = OrderBy.DESC,
):
    return await GroupService.get_groups(
        db,
        pagination.skip,
        pagination.limit,
        filters,
        sort_by,
        order,
    )


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_by_id(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
):
    return await GroupService.get_group_by_id(db, group_id)


@router.get("/{group_id}/students", response_model=PaginatedResponse[UserResponseAdmin])
async def get_group_students(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    pagination: pagination_dependency,
    group_id: Annotated[int, Path(ge=1)],
):
    return await GroupService.get_students(
        db, group_id, pagination.skip, pagination.limit
    )


@router.post(
    "/{group_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def add_student_to_group(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
    student_id: Annotated[int, Path(ge=1)],
):
    await GroupService.add_student_to_group(db, current_user.id, group_id, student_id)


@router.delete(
    "/{group_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_student_from_group(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
    student_id: Annotated[int, Path(ge=1)],
):
    await GroupService.remove_student_from_group(
        db, current_user.id, group_id, student_id
    )
