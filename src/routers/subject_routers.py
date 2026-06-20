from fastapi import APIRouter, status

from src.schemas.subject_schemas import (
    SubjectResponseAdmin,
    SubjectCreateAdmin,
    SubjectUpdateInfoAdmin,
)

from database import db_dependency
from core.security import user_dependency
from src.services.subject_services import SubjectService


router = APIRouter(tags=["Subjects"])


@router.post(
    "/subjects",
    response_model=SubjectResponseAdmin,
    status_code=status.HTTP_201_CREATED,
)
def add_subject(
    db: db_dependency, user: user_dependency, subject_request: SubjectCreateAdmin
):

    return SubjectService.add_subject(db, user, subject_request)


@router.delete("/subjects/{subject_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def remove_subject(db: db_dependency, user: user_dependency, subject_id: int):

    SubjectService.remove_subject(db, user, subject_id)


@router.put(
    "/subjects/{subject_id}/update",
    response_model=SubjectResponseAdmin,
    status_code=status.HTTP_200_OK,
)
def update_subject_info(
    db: db_dependency,
    user: user_dependency,
    subject_id: int,
    subject_update_info_request: SubjectUpdateInfoAdmin,
):

    return SubjectService.update_subject_info(
        db, user, subject_id, subject_update_info_request
    )


@router.get(
    "/subjects",
    response_model=list[SubjectResponseAdmin],
    status_code=status.HTTP_200_OK,
)
def get_subjects(db: db_dependency, user: user_dependency):

    return SubjectService.get_subjects(db, user)
