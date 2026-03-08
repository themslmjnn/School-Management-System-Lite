from fastapi import APIRouter, Depends, Path

from sqlalchemy.orm import Session

from passlib.context import CryptContext

from starlette import status
from typing import Annotated

from db.database import get_db
from src.schemas.user_schemas import *
from src.services.user_services import UserService

router = APIRouter(
    tags=["Users"]
)


db_dependency = Annotated[Session, Depends(get_db)]

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

path_param_int_ge1 = Annotated[int, Path(ge=1)]


@router.post("/admin/users_registration", response_model=UserResponseAdmin, status_code=status.HTTP_201_CREATED)
def admin_register_user(
        db: db_dependency,
        user_request: UserCreateAdmin):

    return UserService.register_user(db, user_request, bcrypt_context)


@router.get("/admin/users", response_model=list[UserResponseAdmin], status_code=status.HTTP_200_OK)
def admin_get_all_users(db: db_dependency):
    return UserService.get_all_users(db)


@router.get("/admin/search_users", response_model=list[UserResponseAdmin], status_code=status.HTTP_200_OK)
def admin_search_users(
        db: db_dependency,
        users_request: Annotated[UserSearchAdmin, Depends()]):
    
    return UserService.search_users(db, users_request)


# @router.get("/director/users", response_model=list[UserResponseDirector], status_code=status.HTTP_200_OK)
# def director_get_all_users(db: db_dependency):
#     return UserService.get_all_users(db)


# @router.get("/director/search_users", response_model=list[UserResponseDirector], status_code=status.HTTP_200_OK)
# def director_search_users(
#         db: db_dependency,
#         users_request: Annotated[UserSearchGeneral, Depends()]):
    
#     return UserService.search_users(db, users_request)


# @router.get("/head_of_class/users", response_model=list[UserResponseHeadOfClass], status_code=status.HTTP_200_OK)
# def head_of_class_get_all_users(db: db_dependency):
#     return UserService.get_all_users(db)


# @router.get("/head_of_class/search_users", response_model=list[UserResponseHeadOfClass], status_code=status.HTTP_200_OK)
# def head_of_class_search_users(
#         db: db_dependency,
#         users_request: Annotated[UserSearchGeneral, Depends()]):
    
#     return UserService.search_users(db, users_request)


@router.put("/admin/update_users_info/{user_id}", response_model=UserResponseAdmin, status_code=status.HTTP_200_OK)
def admin_update_user_info(
        db: db_dependency,
        user_id: path_param_int_ge1,
        user_request: UserUpdateInfoAdmin):
    
    return UserService.update_user_info(db, user_id, user_request)


@router.put("/admin/update_users_password/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_update_user_password(
        db: db_dependency,
        user_id: path_param_int_ge1,
        user_password_request: UserUpdatePasswordAdmin):
    
    UserService.update_user_password(db, user_id, user_password_request, bcrypt_context)