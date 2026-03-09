from fastapi import APIRouter, Depends, Path

from sqlalchemy.orm import Session

from passlib.context import CryptContext

from starlette import status
from typing import Annotated

from db.database import get_db
from core.security import get_current_user
from src.schemas.user_schemas import UserResponseAdmin, UserResponseGeneral, UserSearchAdmin, UserSearchGeneral, UserUpdateInfoAdmin, UserUpdatePasswordAdmin
from src.services.user_services import UserService


router = APIRouter(
    tags=["Users"]
)

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

path_param_int_ge1 = Annotated[int, Path(ge=1)]



@router.get("/users", response_model=list[UserResponseAdmin], status_code=status.HTTP_200_OK)
def get_users(
        db: db_dependency,
        user: user_dependency):
    
    return UserService.get_users(db, user)



@router.get("/users_search", response_model=list[UserResponseAdmin], status_code=status.HTTP_200_OK)
def search_users(
        db: db_dependency,
        user: user_dependency,
        users_request: Annotated[UserSearchAdmin, Depends()]):
    
    return UserService.search_users(db, user, users_request)



@router.put("/users/{user_id}/update_info", response_model=UserResponseAdmin, status_code=status.HTTP_200_OK)
def update_user_info(
        db: db_dependency,
        user: user_dependency,
        user_id: path_param_int_ge1,
        user_request: UserUpdateInfoAdmin):
    
    return UserService.update_user_info(db, user, user_id, user_request)



@router.put("/users/{user_id}/update_password", status_code=status.HTTP_204_NO_CONTENT)
def update_user_password(
        db: db_dependency,
        user: user_dependency,
        user_id: path_param_int_ge1,
        user_password_request: UserUpdatePasswordAdmin):
    
    UserService.update_user_password(db, user, user_id, user_password_request, bcrypt_context)