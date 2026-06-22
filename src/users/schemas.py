from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator

from src.utils import validators
from src.utils.base_schema import BaseSchema
from src.utils.enums import UserRole, UserStatus


class CreateUserAdmin(BaseModel):
    username: str = Field(min_length=6, max_length=20)
    firstname: str = Field(min_length=2, max_length=50)
    lastname: str = Field(min_length=2, max_length=50)
    middlename: str | None = Field(min_length=2, max_length=50, default=None)
    date_of_birth: date
    phone_number: str
    email: EmailStr
    address: str | None = Field(min_length=15, max_length=100, default=None)
    role: UserRole

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return validators.validate_username(v)

    @field_validator("firstname")
    @classmethod
    def validate_firstname(cls, v: str) -> str:
        return validators.validate_firstname(v)

    @field_validator("lastname")
    @classmethod
    def validate_lastname(cls, v: str) -> str:
        return validators.validate_lastname(v)

    @field_validator("middlename")
    @classmethod
    def validate_middlename(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return validators.validate_middlename(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        return validators.validate_date_of_birth(v)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        return validators.validate_phone_number(v)


class UserResponseAdmin(BaseSchema):
    id: int
    firstname: str
    lastname: str
    middlename: str
    role: UserRole


class UserResponseAdminDetailed(UserResponseAdmin):
    date_of_birth: date
    phone_number: str
    email: EmailStr
    address: str
    status: UserStatus
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")
