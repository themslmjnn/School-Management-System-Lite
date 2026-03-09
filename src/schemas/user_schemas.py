from pydantic import BaseModel, Field, EmailStr, ConfigDict

from typing import Optional
from datetime import date, datetime

from src.models.user_model import UserRole


class UserBase(BaseModel):
    username: str = Field(min_length=6, max_length=20)
    first_name: str = Field(max_length=30)
    last_name: str = Field(max_length=30)

    date_of_birth: date
    address: str = Field(max_length=100)

    email: EmailStr
    phone_number: str = Field(min_length=6, max_length=30)


class UserCreateAdmin(UserBase):
    password: str = Field(min_length=8)


class UserResponseAdmin(UserBase):
    id: int

    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponseGeneral(UserBase):
    id: int

    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)



class UserUpdateInfoBase(BaseModel):
    username: Optional[str] = Field(min_length=6, max_length=20, default=None)
    first_name: Optional[str] = Field(min_length=2, max_length=30, default=None)
    last_name: Optional[str] = Field(min_length=2, max_length=30, default=None)

    date_of_birth: Optional[date] = Field(default=None)
    address: Optional[str] = Field(max_length=100, default=None)

    email: Optional[EmailStr] = Field(default=None)
    phone_number: Optional[str] = Field(min_length=6, max_length=30, default=None)


class UserUpdateInfoAdmin(UserUpdateInfoBase):
    role: UserRole = Field(default=None)


class UserUpdatePasswordBase(BaseModel):
    old_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class UserUpdatePasswordGeneral(UserUpdatePasswordBase):
    pass


class UserUpdatePasswordAdmin(UserUpdatePasswordBase):
    pass
    

class UserSearchBase(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    date_of_birth: Optional[date] = None

    role: Optional[UserRole] = None
    
    is_active: Optional[bool] = None


class UserSearchGeneral(UserSearchBase):
    pass


class UserSearchAdmin(UserSearchBase):
    pass