from pydantic import BaseModel, Field, EmailStr, field_validator

from typing import Optional
from datetime import date, datetime

from models.user import UserRole
from src.schemas.base_schema import BaseSchema
from src.utils import validators as field_validators


class UserBase(BaseModel):
    username: str = Field(min_length=6, max_length=20)
    first_name: str = Field(min_length=2, max_length=30)
    last_name: str = Field(min_length=2, max_length=30)
    email: EmailStr
    phone_number: str
    date_of_birth: date
    citizenship: str
    address: str = Field(max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, username: str) -> str:
        return field_validators.validate_username(username)

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, field: str) -> str:
        return field_validators.validate_first_name(field)

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, field: str) -> str:
        return field_validators.validate_last_name(field)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, field: date) -> date:
        return field_validators.validate_date_of_birth(field)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, field: str) -> str:
        return field_validators.validate_phone_number(field)


class CreateUserAdmin(UserBase):
    role: UserRole


class UserResponseAdmin(UserBase, BaseSchema):
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

    is_active: Optional[bool] = Field(default=None)


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
