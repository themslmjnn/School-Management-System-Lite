from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status

from pagination import PaginatedResponse
from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    pagination_dependency,
    require_directors,
)
from src.core.limiter import user_limiter
from users.schemas.users import (
    SearchUserAdmin,
    UserResponseAdmin,
    UserResponseAdminDetailed,
)
from users.services.user_management import UserServiceAdmin, UserServiceStaff
from utils.enums import OrderBy, UserSortField

router = APIRouter(
    prefix="director/users",
    tags=["Users - Director"],
)


@router.get(
    "",
    response_model=PaginatedResponse[UserResponseAdmin],
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("15/minute")
async def get_users(
    request: Request,
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_directors)],
    pagination: pagination_dependency,
    filters: Annotated[SearchUserAdmin, Depends()],
    sort_by: str = UserSortField.created_at,
    order: str = OrderBy.desc,
):
    return await UserServiceStaff.get_users(
        db,
        pagination.skip,
        pagination.limit,
        filters,
        sort_by,
        order,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponseAdminDetailed | dict,
    status_code=status.HTTP_200_OK,
)
async def get_user_by_id(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_directors)],
    user_id: Annotated[int, Path(ge=1)],
):
    return await UserServiceAdmin.get_user_by_id(db, user_id)


@router.get("/parents")
async def get_parents(): ...


@router.get("/parents/{parent_id}")
async def get_parent_by_id(): ...


@router.get("/students")
async def get_students(): ...


@router.get("/students/{student_id}")
async def get_student_by_id(): ...
