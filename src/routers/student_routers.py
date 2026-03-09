from fastapi import APIRouter, Depends

from starlette import status
from typing import Annotated

from core.security import user_dependency, bcrypt_context
from db.database import db_dependency
from src.schemas.student_schemas import StudentCreateAdmin, StudentResponseAdmin, StudentResponseGeneral, StudentResponseBase, StudentUpdateInfoAdmin
from src.services.student_services import StudentService


router = APIRouter(tags=["Students"])


@router.post("/students", response_model=StudentResponseAdmin, status_code=status.HTTP_201_CREATED)
def register_student(
        db: db_dependency,
        user: user_dependency,
        student_request: StudentCreateAdmin):

    return StudentService.register_student(db, user, student_request, bcrypt_context)



@router.get("/students", response_model=list[StudentResponseAdmin], status_code=status.HTTP_200_OK)
def get_students(
        db: db_dependency,
        user: user_dependency):
    
    return StudentService.get_students_admin(db, user)



@router.put("/students/{student_id}/update", response_model=StudentResponseBase, status_code=status.HTTP_200_OK)
def update_student_info(
        db: db_dependency,
        user: user_dependency,
        student_id: int,
        student_update_info_request: StudentUpdateInfoAdmin):
    
    return StudentService.update_student_info(db, user, student_id, student_update_info_request)


@router.put("/students/{student_id}/graduate", status_code=status.HTTP_204_NO_CONTENT)
def graduate_student(
        db: db_dependency,
        user: user_dependency,
        student_id: int):
    
    return StudentService.graduate_student(db, user, student_id)


@router.put("/students/{student_id}/drop", status_code=status.HTTP_204_NO_CONTENT)
def drop_student(
        db: db_dependency,
        user: user_dependency,
        student_id: int):
    
    return StudentService.drop_student(db, user, student_id)


# @router.post("/students/subjects", response_model=StudentSubjectResponseAdmin, status_code=status.HTTP_201_CREATED)
# def enroll_student_in_subject(db: db_dependency, user: user_dependency, student_subject_request: StudentSubjectCreateAdmin):
#     return CoreService.add(db, user, student_subject_request)


# @router.delete("/students/subjects/{enrollment_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
# def withdraw_student_subject(db: db_dependency, user: user_dependency, student_subject_id: int):
#     CoreService.delete(db, user, student_subject_id)


# @router.put("/students/subjects/{enrollment_id}/update", response_model=StudentSubjectResponseAdmin, status_code=status.HTTP_200_OK)
# def update_student_subject(db: db_dependency, user: user_dependency, student_subject_id: int, student_subject_update_info_request: StudentSubjectUpdateInfoAdmin):
#     return CoreService.update(db, user, student_subject_id, student_subject_update_info_request)


# @router.get("/students/subjects", response_model=list[StudentSubjectResponseAdmin], status_code=status.HTTP_200_OK)
# def get_students_subjects(db: db_dependency, user: user_dependency,):
#     return CoreService.get_student_subjects(db, user)
    



# @router.post("/students/groups", response_model=StudentGroupResponseAdmin, status_code=status.HTTP_201_CREATED)
# def add_student_to_group(db: db_dependency, user: user_dependency, student_group_request: StudentGroupCreateAdmin):
#     return CoreService.add(db, user, student_group_request)


# @router.delete("/students/groups/{enrollment_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
# def delete_student_from_group(db: db_dependency, user: user_dependency, student_group_id: int):
#     CoreService.delete(db, user, student_group_id)


# @router.put("/students/groups/{enrollment_id}/update", response_model=StudentGroupResponseAdmin, status_code=status.HTTP_200_OK)
# def update_student_group(db: db_dependency, user: user_dependency, student_group_id: int, student_group_update_info_request: StudentGroupUpdateInfoAdmin):
#     return CoreService.update(db, user, student_group_id, student_group_update_info_request)


# @router.get("/students/groups", response_model=list[StudentGroupResponseAdmin], status_code=status.HTTP_200_OK)
# def get_students_groups(db: db_dependency, user: user_dependency,):
#     return CoreService.get_student_groups(db, user)
