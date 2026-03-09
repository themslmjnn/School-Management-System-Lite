from fastapi import APIRouter, Depends, Path

from sqlalchemy.orm import Session

from starlette import status
from typing import Annotated

from core.security import get_current_user
from db.database import get_db
from src.schemas.student_schemas import StudentCreateAdmin, StudentResponseAdmin, StudentResponseGeneral, StudentResponseBase, StudentUpdateInfoAdmin
from src.services.student_services import StudentService
from routers.user_routers import bcrypt_context


router = APIRouter(
    tags=["Students"]
)

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

path_param_ge1 = Annotated[int, Path(ge=1)]


# Done
@router.post("/students", response_model=StudentResponseAdmin, status_code=status.HTTP_201_CREATED)
def register_student(
        db: db_dependency,
        user: user_dependency,
        student_request: StudentCreateAdmin):

    return StudentService.register_student(db, user, student_request, bcrypt_context)


# Done
@router.get("/students", response_model=list[StudentResponseAdmin], status_code=status.HTTP_200_OK)
def get_students(
        db: db_dependency,
        user: user_dependency):
    
    return StudentService.get_students_admin(db, user)



@router.put("/students/{student_id}/update", response_model=StudentResponseBase, status_code=status.HTTP_200_OK)
def update_student_info(
        db: db_dependency,
        user: user_dependency,
        student_id: path_param_ge1,
        student_update_info_request: StudentUpdateInfoAdmin):
    
    return StudentService.update_student_info(db, user, student_id, student_update_info_request)


@router.put("/students/{student_id}/graduate", status_code=status.HTTP_204_NO_CONTENT)
def graduate_student(
        db: db_dependency,
        user: user_dependency,
        student_id: path_param_ge1):
    
    return StudentService.graduate_student(db, user, student_id)


@router.put("/students/{student_id}/drop", status_code=status.HTTP_204_NO_CONTENT)
def drop_student(
        db: db_dependency,
        user: user_dependency,
        student_id: path_param_ge1):
    
    return StudentService.drop_student(db, user, student_id)


@router.post("/students/subjects", response_model=StudentSubjectResponseAdmin, status_code=status.HTTP_201_CREATED)
def enroll_student_in_subject(db: db_dependency, user: user_dependency, student_subject_request: StudentSubjectCreateAdmin):
    return CoreService.add(db, user, student_subject_request)


@router.delete("/students/subjects/{enrollment_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_student_subject(db: db_dependency, user: user_dependency, student_subject_id: path_param_ge1):
    CoreService.delete(db, user, student_subject_id)


@router.put("/students/subjects/{enrollment_id}/update", response_model=StudentSubjectResponseAdmin, status_code=status.HTTP_200_OK)
def update_student_subject(db: db_dependency, user: user_dependency, student_subject_id: path_param_ge1, student_subject_update_info_request: StudentSubjectUpdateInfoAdmin):
    return CoreService.update(db, user, student_subject_id, student_subject_update_info_request)


@router.get("/students/subjects", response_model=list[StudentSubjectResponseAdmin], status_code=status.HTTP_200_OK)
def get_students_subjects(db: db_dependency, user: user_dependency,):
    return CoreService.get_student_subjects(db, user)
    



@router.post("/admin/student_group_addition", response_model=StudentGroupResponseAdmin, status_code=status.HTTP_201_CREATED)
def add_student_group_admin(db: db_dependency, user: user_dependency, student_group_request: StudentGroupCreateAdmin):
    return CoreService.add(db, user, student_group_request)


@router.delete("/admin/student_group_deletion/{student_group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_group_admin(db: db_dependency, user: user_dependency, student_group_id: path_param_ge1):
    CoreService.delete(db, user, student_group_id)


@router.put("/admin/student_group_updating_indo/{student_group_id}", response_model=StudentGroupResponseAdmin, status_code=status.HTTP_200_OK)
def update_student_group_info_admin(db: db_dependency, user: user_dependency, student_group_id: path_param_ge1, student_group_update_info_request: StudentGroupUpdateInfoAdmin):
    return CoreService.update(db, user, student_group_id, student_group_update_info_request)


@router.get("/admin/student_groups", response_model=list[StudentGroupResponseAdmin], status_code=status.HTTP_200_OK)
def get_student_groups(db: db_dependency, user: user_dependency,):
    return CoreService.get_student_groups(db, user)
