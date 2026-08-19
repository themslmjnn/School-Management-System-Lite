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
from src.subjects.schemas import (
    SearchSubjectBase,
    SubjectResponseBase,
    SubjectResponseDirectorDetailed,
)
from src.subjects.services.director import SubjectServiceDirector
from src.utils.enums import OrderBy, SubjectSortField

router = APIRouter(
    prefix="/director/subjects",
    tags=["Subjects - Director"],
)


@router.get(
    "",
    response_model=PaginatedResponse[SubjectResponseBase],
    status_code=status.HTTP_200_OK,
)
@user_limiter.limit("15/minute")
async def get_subjects(
    request: Request,
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_director)],
    pagination: pagination_dependency,
    filters: Annotated[SearchSubjectBase, Depends()],
    sort_by: str = SubjectSortField.NAME,
    order: str = OrderBy.ASC,
):
    return await SubjectServiceDirector.get_subjects(
        session, pagination.skip, pagination.limit, filters, sort_by, order
    )


@router.get(
    "/{subject_id}",
    response_model=SubjectResponseDirectorDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_subject_by_id(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_director)],
    subject_id: Annotated[int, Path(ge=1)],
):
    return await SubjectServiceDirector.get_subject_by_id(session, subject_id)
