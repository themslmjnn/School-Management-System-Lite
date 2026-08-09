from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.academics.schemas.student_subject_enrollment import (
    StudentSubjectEnrollmentResponse,
)
from src.academics.services.student_subject_enrollment import (
    StudentSubjectEnrollmentService,
)
from src.core.dependencies import CurrentUser, async_db_dependency, require_system_admin

student_subjects_router = APIRouter(
    prefix="/students",
    tags=["Student Subject Enrollment - System Admin"],
)


@student_subjects_router.get(
    "/{student_id}/subjects",
    response_model=list[StudentSubjectEnrollmentResponse],
)
async def get_student_subjects(
    db: async_db_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    student_id: Annotated[int, Path(ge=1)],
):
    return await StudentSubjectEnrollmentService.get_enrolled_subjects(db, student_id)


@student_subjects_router.post(
    "/{student_id}/subjects/{subject_id}",
    response_model=StudentSubjectEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_student_in_subject(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    student_id: Annotated[int, Path(ge=1)],
    subject_id: Annotated[int, Path(ge=1)],
):
    return await StudentSubjectEnrollmentService.enroll_student(
        db, current_user.id, student_id, subject_id
    )


@student_subjects_router.delete(
    "/{student_id}/subjects/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unenroll_student_from_subject(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    student_id: Annotated[int, Path(ge=1)],
    subject_id: Annotated[int, Path(ge=1)],
):
    await StudentSubjectEnrollmentService.unenroll_student(
        db, current_user.id, student_id, subject_id
    )
