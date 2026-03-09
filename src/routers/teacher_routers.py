from fastapi import APIRouter, Depends, Path

from sqlalchemy.orm import Session

from typing import Annotated
from starlette import status

from core.security import get_current_user
from db.database import get_db
from src.schemas.teacher_schemas import TeacherCreateAdmin, TeacherResponseAdmin, TeacherResponseGeneral, TeacherUpdateInfoBase
from src.services.teacher_services import TeacherService
from src.routers.user_router import bcrypt_context


router = APIRouter(
    tags=["Teacher"]
)

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

path_param_ge1 = Annotated[int, Path(ge=1)]


@router.post("/admin/teachers_registration", response_model=TeacherResponseAdmin, status_code=status.HTTP_201_CREATED)
def register_teacher_admin(
        db: db_dependency,
        user: user_dependency,
        teacher_request: TeacherCreateAdmin):
    
    return TeacherService.register_teacher(db, user, teacher_request, bcrypt_context)


@router.get("/admin/teachers", response_model=list[TeacherResponseAdmin], status_code=status.HTTP_200_OK)
def get_teachers_admin(
        db: db_dependency,
        user: user_dependency):
    
    return TeacherService.get_teachers_admin(db, user)



@router.get("/general/teachers", response_model=list[TeacherResponseGeneral], status_code=status.HTTP_200_OK)
def get_teachers_general(
        db: db_dependency,
        user: user_dependency):
    
    return TeacherService.get_teachers_general(db, user)



@router.put("/admin/teachers_updating_info/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_teacher_info_admin(
        db: db_dependency,
        user: user_dependency,
        teacher_id: path_param_ge1,
        teacher_update_info_request: TeacherUpdateInfoBase):
    
    return TeacherService.update_teacher_info_admin(db, user, teacher_id, teacher_update_info_request)


@router.put("/admin/dropping_teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def drop_teacher_admin(
    db: db_dependency, user: user_dependency, teacher_id: path_param_ge1):

    return TeacherService.drop_teacher_admin(db, user, teacher_id)


@router.put("/admin/firing_teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def fire_teacher_admin(db: db_dependency, user: user_dependency, teacher_id: path_param_ge1):

    return TeacherService.fire_teacher_admin(db, user, teacher_id)