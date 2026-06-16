from fastapi import APIRouter

from starlette import status
from typing import Union

from database import db_dependency
from core.security import user_dependency, bcrypt_context
from src.schemas.student_schemas import StudentCreateAdmin, StudentResponseAdmin, StudentResponsePublic, StudentUpdateInfoAdmin, StudentUpdateInfoResponseAdmin
from src.schemas.student_schemas import StudentSubjectCreateAdmin, StudentSubjectResponseAdmin, StudentSubjectUpdateInfoAdmin
from src.schemas.student_schemas import StudentGroupCreateAdmin, StudentGroupUpdateInfoAdmin, StudentGroupResponseAdmin
from src.services.student_services import StudentService


router = APIRouter(
    tags=["Students"]
)


# Working with Students endpoints

# Register student
@router.post("/students", response_model=StudentResponseAdmin, status_code=status.HTTP_201_CREATED)
def register_student(
        db: db_dependency,
        user: user_dependency,
        student_request: StudentCreateAdmin):

    return StudentService.register_student(db, user, student_request, bcrypt_context)


# Read all students
@router.get("/students", response_model=list[Union[StudentResponseAdmin, StudentResponsePublic]], status_code=status.HTTP_200_OK)
def get_students(
        db: db_dependency,
        user: user_dependency):
    
    return StudentService.get_students(db, user)


# Update student info
@router.put("/students/{student_id}/update", response_model=StudentUpdateInfoResponseAdmin, status_code=status.HTTP_200_OK)
def update_student_info(
        db: db_dependency,
        user: user_dependency,
        student_id: int,
        student_update_info_request: StudentUpdateInfoAdmin):
    
    return StudentService.update_student_info(db, user, student_id, student_update_info_request)


# Updating student status to graduated
# @router.put("/students/{student_id}/graduate", status_code=status.HTTP_204_NO_CONTENT)
# def graduate_student(
#         db: db_dependency,
#         user: user_dependency,
#         student_id: int):
    
#     StudentService.graduate_student(db, user, student_id)


# Updating student status to dropped
# @router.put("/students/{student_id}/drop", status_code=status.HTTP_204_NO_CONTENT)
# def drop_student(
#         db: db_dependency,
#         user: user_dependency,
#         student_id: int):
    
#     StudentService.drop_student(db, user, student_id)


# Working with Students and Subjects endpoints

# Enrolling student in subject
@router.post("/students/subjects", response_model=StudentSubjectResponseAdmin, status_code=status.HTTP_201_CREATED)
def enroll_student_in_subject(
        db: db_dependency, 
        user: user_dependency, 
        student_subject_request: StudentSubjectCreateAdmin):
    
    return StudentService.enroll_student_in_subject(db, user, student_subject_request)


# Withdraw student from subject
# @router.put("/students/subjects/{enrollment_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
# def withdraw_student_subject(
#         db: db_dependency, 
#         user: user_dependency, 
#         enrollment_id: int):

#     StudentService.withdraw_student_subject_enrollment(db, user, enrollment_id)


# Update student subject enrollments info
@router.put("/students/subjects/{enrollment_id}/update", response_model=StudentSubjectResponseAdmin, status_code=status.HTTP_200_OK)
def update_student_subject(
        db: db_dependency, 
        user: user_dependency, 
        enrollment_id: int, 
        enrollment_update_info_request: StudentSubjectUpdateInfoAdmin):
    
    return StudentService.update_student_subject(db, user, enrollment_id, enrollment_update_info_request)


# Read all students enrolled in subjects
@router.get("/students/subjects", response_model=list[StudentSubjectResponseAdmin], status_code=status.HTTP_200_OK)
def get_students_subjects(
        db: db_dependency,
        user: user_dependency):

    return StudentService.get_students_subjects(db, user)
    

# Working with Students and Groups endpoints

# Adding student to group
@router.post("/students/groups", response_model=StudentGroupResponseAdmin, status_code=status.HTTP_201_CREATED)
def add_student_to_group(
        db: db_dependency, 
        user: user_dependency, 
        student_group_request: StudentGroupCreateAdmin):
    
    return StudentService.add_student_to_group(db, user, student_group_request)


# # Removing student from group
# @router.put("/students/groups/{enrollment_id}/remove", status_code=status.HTTP_204_NO_CONTENT)
# def remove_student_from_group(
#         db: db_dependency, 
#         user: user_dependency, 
#         enrollment_id: int):
    
#     StudentService.remove_student_from_group(db, user, enrollment_id)


# Updating student group enrollment info
@router.put("/students/groups/{enrollment_id}/update", response_model=StudentGroupResponseAdmin, status_code=status.HTTP_200_OK)
def update_student_group(
        db: db_dependency, 
        user: user_dependency, 
        enrollment_id: int, 
        student_group_update_info_request: StudentGroupUpdateInfoAdmin):
    
    return StudentService.update_student_group(db, user, enrollment_id, student_group_update_info_request)


# Reading all students added to groups
@router.get("/students/groups", response_model=list[StudentGroupResponseAdmin], status_code=status.HTTP_200_OK)
def get_students_groups(
        db: db_dependency, 
        user: user_dependency):
    
    return StudentService.get_students_groups(db, user)