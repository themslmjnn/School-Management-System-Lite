from fastapi import APIRouter, status, Depends, Path

from src.schemas.subject_schemas import SubjectResponseAdmin, SubjectCreateAdmin, SubjectUpdateInfoAdmin

from typing import Annotated
from sqlalchemy.orm import Session
from db.database import get_db
from src.services.subject_services import SubjectService
from core.security import get_current_user
router = APIRouter(
    tags=["Subjects"]
)

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

path_param_ge1 = Annotated[int, Path(ge=1)]

@router.post("/admin/subject_addition", response_model=SubjectResponseAdmin, status_code=status.HTTP_201_CREATED)
def add_subject_admin(db: db_dependency, user: user_dependency, subject_request: SubjectCreateAdmin):
    return SubjectService.add_subject_admin(db, user, subject_request)


@router.delete("/admin/subject_deletion/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject_admin(db: db_dependency, user: user_dependency, subject_id: path_param_ge1):
    SubjectService.delete_subject_admin(db, user, subject_id)


@router.put("/admin/subject_updating_indo/{subject_id}", response_model=SubjectResponseAdmin, status_code=status.HTTP_200_OK)
def update_subject_info_admin(db: db_dependency, user: user_dependency, subject_id: path_param_ge1, subject_update_info_request: SubjectUpdateInfoAdmin):
    return SubjectService.update_subject_info_admin(db, user, subject_id, subject_update_info_request)


@router.get("/admin/subjects", response_model=list[SubjectResponseAdmin], status_code=status.HTTP_200_OK)
def get_subjects(db: db_dependency, user: user_dependency,):
    return SubjectService.get_subjects_admin(db, user)
    