from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    computed_field,
    field_serializer,
    field_validator,
)

from src.utils import validators
from src.utils.base_schema import BaseSchema
from src.utils.enums import UserRole, UserStatus


# COMPLETED!!!
class CreateUserBase(BaseModel):
    username: str = Field(min_length=6, max_length=20)
    firstname: str = Field(min_length=3, max_length=50)
    lastname: str = Field(min_length=3, max_length=50)
    middlename: str | None = Field(min_length=2, max_length=50, default=None)
    phone_number: str
    email: EmailStr

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

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        return validators.parse_and_validate_mobile_number(v)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return v.strip().lower()


# COMPLETED!!!
class CreateStudentAdmin(CreateUserBase):
    type: Literal["student"] = "student"
    date_of_birth: date
    address: str | None = Field(min_length=15, max_length=100, default=None)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        return validators.validate_date_of_birth(v)


# COMPLETED!!!
class CreateStaffAdmin(CreateUserBase):
    type: Literal["staff"] = "staff"
    role: UserRole


# COMPLETED!!!
class CreateGuardianAdmin(CreateUserBase):
    type: Literal["guardian"] = "guardian"


# COMPLETED!!!
CreateRequest = Annotated[
    CreateStudentAdmin | CreateStaffAdmin | CreateGuardianAdmin,
    Field(discriminator="type"),
]


# COMPLETED!!!
class UserResponseAdmin(BaseModel):
    firstname: str
    lastname: str
    middlename: str | None
    role: UserRole


# COMPLETED!!!
class UserResponseAdminDetailed(UserResponseAdmin, BaseSchema):
    id: int
    username: str
    date_of_birth: date | None
    phone_number: str = Field(exclude=True)
    email: EmailStr
    address: str | None
    status: UserStatus
    is_active: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")

    @computed_field
    @property
    def format_phone_number(self) -> str:
        return validators.format_phone_for_display(self.phone_number)
