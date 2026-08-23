from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    pagination_dependency,
    require_system_admin,
)
from src.core.pagination import PaginatedResponse
from src.subjects.schemas import (
    CreateSubjectAdmin,
    SearchSubjectAdmin,
    SubjectResponseAdminDetailed,
    SubjectResponseBase,
    UpdateSubjectAdmin,
)
from src.subjects.services.system_admin import SubjectServiceAdmin
from src.utils.enums import OrderBy, SubjectSortField

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects - System Admin"],
)


@router.post(
    "", response_model=SubjectResponseAdminDetailed, status_code=status.HTTP_201_CREATED
)
async def create_subject(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: CreateSubjectAdmin,
):
    return await SubjectServiceAdmin.create_subject(
        session, current_user.id, create_request
    )


@router.patch("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_subject(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    subject_id: Annotated[int, Path(ge=1)],
    update_request: UpdateSubjectAdmin,
):
    await SubjectServiceAdmin.update_subject(
        session, current_user.id, subject_id, update_request
    )


@router.patch("/{subject_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_subject(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    subject_id: Annotated[int, Path(ge=1)],
):
    await SubjectServiceAdmin.archive_subject(session, current_user.id, subject_id)


@router.patch("/{subject_id}/restoration", status_code=status.HTTP_204_NO_CONTENT)
async def restore_subject(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    subject_id: Annotated[int, Path(ge=1)],
):
    await SubjectServiceAdmin.restore_subject(session, current_user.id, subject_id)


@router.get(
    "",
    response_model=PaginatedResponse[SubjectResponseBase],
    status_code=status.HTTP_200_OK,
)
async def get_subjects(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    pagination: pagination_dependency,
    filters: Annotated[SearchSubjectAdmin, Depends()],
    sort_by: Annotated[SubjectSortField, Query()] = SubjectSortField.NAME,
    order: Annotated[OrderBy, Query()] = OrderBy.ASC,
):
    return await SubjectServiceAdmin.get_subjects(
        session, pagination.skip, pagination.limit, filters, sort_by, order
    )


@router.get(
    "/{subject_id}",
    response_model=SubjectResponseAdminDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_subject_by_id(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    subject_id: Annotated[int, Path(ge=1)],
):
    return await SubjectServiceAdmin.get_subject_by_id(session, subject_id)
