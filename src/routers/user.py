from typing import Annotated, Union

from fastapi import APIRouter, Depends, status

from src.core.dependencies import async_db_dependency, require_system_admin
from src.core.security import bcrypt_context, user_dependency
from src.models.user import User
from src.schemas.user import (
    CreateUserAdmin,
    UserResponseAdmin,
    UserResponsePublic,
    UserSearchAdmin,
    UserUpdateInfoAdmin,
    UserUpdatePasswordAdmin,
)
from src.services.user import UserService, UserServiceAdmin

router = APIRouter(tags=["Users"])


@router.post("", response_model=UserResponseAdmin, status_code=status.HTTP_201_CREATED)
async def create_user(
    db: async_db_dependency,
    _: Annotated[User, Depends(require_system_admin)],
    create_request: CreateUserAdmin,
):
    return UserServiceAdmin.create_user(db, create_request)


# @router.get(
#     "/users",
#     response_model=list[Union[UserResponseAdmin, UserResponsePublic]],
#     status_code=status.HTTP_200_OK,
# )
# def get_users(db: db_dependency, user: user_dependency):

#     return UserService.get_users(db, user)


# # Search users
# @router.get(
#     "/users/search",
#     response_model=list[UserResponseAdmin],
#     status_code=status.HTTP_200_OK,
# )
# def search_users(
#     db: db_dependency,
#     user: user_dependency,
#     users_request: Annotated[UserSearchAdmin, Depends()],
# ):

#     return UserService.search_users(db, user, users_request)


# # Update user info
# @router.put(
#     "/users/{user_id}/update_info",
#     response_model=UserResponseAdmin,
#     status_code=status.HTTP_200_OK,
# )
# def update_user_info(
#     db: db_dependency,
#     user: user_dependency,
#     user_id: int,
#     user_request: UserUpdateInfoAdmin,
# ):

#     return UserService.update_user_info(db, user, user_id, user_request)


# # Update user password
# @router.put("/users/{user_id}/update_password", status_code=status.HTTP_204_NO_CONTENT)
# def update_user_password(
#     db: db_dependency,
#     user: user_dependency,
#     user_id: int,
#     user_password_request: UserUpdatePasswordAdmin,
# ):

#     UserService.update_user_password(
#         db, user, user_id, user_password_request, bcrypt_context
#     )
