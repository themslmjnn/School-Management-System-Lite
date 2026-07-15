from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from pagination import PaginatedResponse
from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    pagination_dependency,
    require_system_admin,
)
from src.subjects.schemas import (
    SearchSubject,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)
from src.subjects.service import SubjectService
from utils.enums import OrderBy, SubjectSortField

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    request: SubjectCreate,
):
    return await SubjectService.create_subject(db, current_user.id, request)


@router.patch(
    "/{subject_id}", response_model=SubjectResponse, status_code=status.HTTP_200_OK
)
async def update_subject(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    subject_id: Annotated[int, Path(ge=1)],
    request: SubjectUpdate,
):
    return await SubjectService.update_subject(db, current_user.id, subject_id, request)


@router.patch("/{subject_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_subject(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    subject_id: Annotated[int, Path(ge=1)],
):
    await SubjectService.archive_subject(db, current_user.id, subject_id)


@router.patch("/{subject_id}/restoration", status_code=status.HTTP_204_NO_CONTENT)
async def restore_subject(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    subject_id: Annotated[int, Path(ge=1)],
):
    await SubjectService.restore_subject(db, current_user.id, subject_id)


@router.get("", response_model=PaginatedResponse[SubjectResponse])
async def get_subjects(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    pagination: pagination_dependency,
    filters: Annotated[SearchSubject, Depends()],
    sort_by: str = SubjectSortField.NAME,
    order: str = OrderBy.ASC,
):
    return await SubjectService.get_subjects(
        db, pagination.skip, pagination.limit, filters, sort_by, order
    )


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject_by_id(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    subject_id: Annotated[int, Path(ge=1)],
):
    return await SubjectService.get_subject_by_id(db, subject_id)
