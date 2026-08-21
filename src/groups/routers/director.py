from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    pagination_dependency,
    require_director,
)
from src.core.limiter import user_limiter
from src.core.pagination import PaginatedResponse
from src.groups.schemas import (
    GroupResponseBase,
    GroupResponseDirectorDetailed,
    SearchGroupBase,
)
from src.groups.services.director import GroupServiceDirector
from src.utils.enums import GroupSortField, OrderBy

router = APIRouter(
    prefix="/director/groups",
    tags=["Groups - Director"],
)


@router.get(
    "",
    response_model=PaginatedResponse[GroupResponseBase],
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("15/minute")
async def get_groups(
    request: Request,
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_director)],
    pagination: pagination_dependency,
    filters: Annotated[SearchGroupBase, Depends()],
    sort_by: str = GroupSortField.ACADEMIC_YEAR,
    order: str = OrderBy.DESC,
):
    return await GroupServiceDirector.get_groups(
        session, pagination.skip, pagination.limit, filters, sort_by, order
    )


@router.get(
    "/{group_id}",
    response_model=GroupResponseDirectorDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_group_by_id(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_director)],
    group_id: Annotated[int, Path(ge=1)],
):
    return await GroupServiceDirector.get_group_by_id(session, group_id)
