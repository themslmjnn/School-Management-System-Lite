from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    pagination_dependency,
    require_director,
)
from src.core.limiter import user_limiter
from src.core.pagination import PaginatedResponse
from src.users.schemas.director import (
    StudentResponseDirector,
    StudentResponseDirectorDetailed,
    UserResponseDirectorDetailed,
)
from src.users.services.director import UserServiceDirector
from src.users.utils.shared_schemas import SearchUserBase, UserResponseBase
from src.utils.enums import OrderBy, UserSortField

router = APIRouter(
    prefix="/director/users",
    tags=["Users - Director"],
)


@router.get(
    "/teachers",
    response_model=PaginatedResponse[UserResponseBase],
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("15/minute")
async def get_teachers(
    request: Request,
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_director)],
    pagination: pagination_dependency,
    filters: Annotated[SearchUserBase, Depends()],
    sort_by: Annotated[UserSortField, Query()] = UserSortField.CREATED_AT,
    order: Annotated[OrderBy, Query()] = OrderBy.DESC,
):
    return await UserServiceDirector.get_teachers(
        session, pagination.skip, pagination.limit, filters, sort_by, order
    )


@router.get(
    "/teachers/{target_teacher_id}",
    response_model=UserResponseDirectorDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_teacher_by_id(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_director)],
    target_teacher_id: Annotated[int, Path(ge=1)],
):
    return await UserServiceDirector.get_teacher_by_id(session, target_teacher_id)


@router.get(
    "/students",
    response_model=PaginatedResponse[StudentResponseDirector],
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("15/minute")
async def get_students(
    request: Request,
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_director)],
    pagination: pagination_dependency,
    filters: Annotated[SearchUserBase, Depends()],
    group_id: int | None = None,
    sort_by: Annotated[UserSortField, Query()] = UserSortField.CREATED_AT,
    order: Annotated[OrderBy, Query()] = OrderBy.DESC,
):
    return await UserServiceDirector.get_students(
        session, pagination.skip, pagination.limit, group_id, filters, sort_by, order
    )


@router.get(
    "/students/{target_student_id}",
    response_model=StudentResponseDirectorDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_student_by_id(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_director)],
    target_student_id: Annotated[int, Path(ge=1)],
):
    return await UserServiceDirector.get_student_by_id(session, target_student_id)
