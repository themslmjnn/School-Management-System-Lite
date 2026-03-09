from fastapi import APIRouter, Depends, Path

from sqlalchemy.orm import Session

from starlette import status
from typing import Annotated

from core.security import get_current_user
from db.database import get_db
from src.schemas.student_schemas import StudentCreateAdmin, StudentResponseAdmin, StudentResponseGeneral, StudentResponseBase, StudentUpdateInfoAdmin
from src.services.student_services import StudentService
from src.routers.user_router import bcrypt_context


router = APIRouter(
    tags=["Student"]
)

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

path_param_ge1 = Annotated[int, Path(ge=1)]


# Done
@router.post("/admin/students_registration", response_model=StudentResponseAdmin, status_code=status.HTTP_201_CREATED)
def admin_register_student(
        db: db_dependency,
        user: user_dependency,
        student_request: StudentCreateAdmin):

    return StudentService.register_student(db, user, student_request, bcrypt_context)


# Done
@router.get("/admin/students", response_model=list[StudentResponseAdmin], status_code=status.HTTP_200_OK)
def get_students_admin(
        db: db_dependency,
        user: user_dependency):
    
    return StudentService.get_students_admin(db, user)



@router.get("/general/students", response_model=list[StudentResponseGeneral], status_code=status.HTTP_200_OK)
def get_students_general(
        db: db_dependency,
        user: user_dependency):
    
    return StudentService.get_students_general(db, user)


# @router.get("/students/{student_id}", response_model=StudentResponseGeneral, status_code=status.HTTP_200_OK)
# def get_student_by_id(
#         db: db_dependency,
#         user: user_dependency,
#         student_id: path_param_ge1):
    
#     return StudentService.get_student_by_id(db, user, student_id)


@router.put("/admin/students_info_updating/{student_id}", response_model=StudentResponseBase, status_code=status.HTTP_200_OK)
def update_student_info_admin(
        db: db_dependency,
        user: user_dependency,
        student_id: path_param_ge1,
        student_update_info_request: StudentUpdateInfoAdmin):
    
    return StudentService.update_student_info(db, user, student_id, student_update_info_request)


@router.put("/admin/students_graduation/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def graduate_student_admin(
        db: db_dependency,
        user: user_dependency,
        student_id: path_param_ge1):
    
    return StudentService.graduate_student(db, user, student_id)


@router.put("/admin/students_dropping/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def drop_student_admin(
        db: db_dependency,
        user: user_dependency,
        student_id: path_param_ge1):
    
    return StudentService.drop_student(db, user, student_id)


