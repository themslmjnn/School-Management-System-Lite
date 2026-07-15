from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.academics.schemas import TeachingAssignmentCreate, TeachingAssignmentResponse
from src.academics.service import TeachingAssignmentService
from src.core.dependencies import CurrentUser, async_db_dependency, require_system_admin

router = APIRouter(prefix="/teaching-assignments", tags=["Teaching Assignments"])


@router.post(
    "", response_model=TeachingAssignmentResponse, status_code=status.HTTP_201_CREATED
)
async def create_teaching_assignment(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    request: TeachingAssignmentCreate,
):
    return await TeachingAssignmentService.create_assignment(
        db, current_user.id, request
    )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teaching_assignment(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    assignment_id: Annotated[int, Path(ge=1)],
):
    await TeachingAssignmentService.delete_assignment(
        db, current_user.id, assignment_id
    )
