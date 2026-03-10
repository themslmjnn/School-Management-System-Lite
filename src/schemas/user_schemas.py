from pydantic import BaseModel, Field

from typing import Optional
from datetime import date, datetime

from src.models.user_model import UserRole
from src.schemas.base_schema import BaseSchema


class UserBase(BaseModel):
    first_name: str = Field(max_length=30)
    last_name: str = Field(max_length=30)

    date_of_birth: date
    address: str = Field(max_length=100)

    phone_number: str = Field(min_length=6, max_length=30)


class UserCreateAdmin(UserBase):
    username: str = Field(min_length=6, max_length=20)
    email: str
    password: str = Field(min_length=8)


class UserResponseAdmin(UserCreateAdmin, BaseSchema):
    id: int

    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserResponsePublic(UserBase, BaseSchema):
    role: UserRole
    is_active: bool


class UserUpdateInfoBase(BaseModel):
    username: Optional[str] = Field(min_length=6, max_length=20, default=None)
    first_name: Optional[str] = Field(min_length=2, max_length=30, default=None)
    last_name: Optional[str] = Field(min_length=2, max_length=30, default=None)

    date_of_birth: Optional[date] = Field(default=None)
    address: Optional[str] = Field(max_length=100, default=None)

    email: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(min_length=6, max_length=30, default=None)


class UserUpdateInfoAdmin(UserUpdateInfoBase):
    role: UserRole = Field(default=None)


class UserUpdatePasswordBase(BaseModel):
    old_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class UserUpdatePasswordPublic(UserUpdatePasswordBase):
    pass


class UserUpdatePasswordAdmin(UserUpdatePasswordBase):
    pass
    

class UserSearchBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    date_of_birth: Optional[date] = None

    role: Optional[UserRole] = None
    
    is_active: Optional[bool] = None


class UserSearchPublic(UserSearchBase):
    pass


class UserSearchAdmin(UserSearchBase):
    username: Optional[str] = None


class CurrentUserResponse(BaseModel):
   username: str = Field(min_length=6, max_length=20)
   id: int
   role: UserRole