from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_system_admin,
)
from src.subjects.schemas import SubjectCreate, SubjectResponse, SubjectUpdate
from src.subjects.service import SubjectService

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
