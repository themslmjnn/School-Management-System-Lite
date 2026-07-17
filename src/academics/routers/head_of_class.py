from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.academics.repositories.head_of_class import HeadOfClassRepository
from src.academics.repositories.teaching_assignment import TeachingAssignmentRepository
from src.academics.schemas.head_of_class import HeadOfClassCreate, HeadOfClassResponse
from src.academics.schemas.teaching_assingment import TeachingAssignmentResponse
from src.academics.services.head_of_class import HeadOfClassService
from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_system_admin,
)

router = APIRouter(
    prefix="/groups",
    tags=["Academics - System Admin"],
)


@router.get(
    "/{group_id}/teaching-assignments",
    response_model=list[TeachingAssignmentResponse],
)
async def get_group_teaching_assignments(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
):
    return await TeachingAssignmentRepository.get_assignment_by_group(db, group_id)


@router.get("/{group_id}/head-of-class", response_model=list[HeadOfClassResponse])
async def get_head_of_class(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
):
    return await HeadOfClassRepository.get_by_group(db, group_id)


@router.post(
    "/{group_id}/head-of-class",
    response_model=HeadOfClassResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_head_of_class(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    group_id: Annotated[int, Path(ge=1)],
    request: HeadOfClassCreate,
):
    return await HeadOfClassService.assign(db, current_user.id, group_id, request)
