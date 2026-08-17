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


class UserResponseAdmin(BaseModel):
    firstname: str
    lastname: str
    middlename: str | None

    role: UserRole


class UserCacheSchema(UserResponseAdmin, BaseSchema):
    id: int

    phone_number: str
    email: str

    date_of_birth: date | None
    address: str | None

    status: UserStatus
    is_active: bool
    created_by: int | None

    created_at: datetime
    updated_at: datetime


class UserResponseAdminDetailed(UserCacheSchema):
    phone_number: str = Field(exclude=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")

    @computed_field
    @property
    def format_phone_number(self) -> str:
        return validators.format_phone_for_display(self.phone_number)


class CreateUserBase(BaseModel):
    username: str = Field(min_length=6, max_length=20)

    firstname: str = Field(min_length=3, max_length=50)
    lastname: str = Field(min_length=3, max_length=50)
    middlename: str | None = Field(min_length=3, max_length=50, default=None)

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


class CreateStudentAdmin(CreateUserBase):
    type: Literal["student"] = "student"

    date_of_birth: date
    address: str | None = Field(min_length=15, max_length=100, default=None)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        return validators.validate_date_of_birth(v)


class CreateTeacherAdmin(CreateUserBase):
    type: Literal["teacher"] = "teacher"


CreateUserRequest = Annotated[
    CreateStudentAdmin | CreateTeacherAdmin,
    Field(discriminator="type"),
]


class UpdateUserBase(BaseModel):
    firstname: str | None = Field(min_length=3, max_length=50, default=None)
    lastname: str | None = Field(min_length=3, max_length=50, default=None)
    middlename: str | None = Field(min_length=3, max_length=50, default=None)

    phone_number: str | None = None

    @field_validator("firstname")
    @classmethod
    def validate_firstname(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return validators.validate_firstname(v)

    @field_validator("lastname")
    @classmethod
    def validate_lastname(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return validators.validate_lastname(v)

    @field_validator("middlename")
    @classmethod
    def validate_middlename(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return validators.validate_middlename(v)

    @field_validator("phone_number", mode="after")
    @classmethod
    def validate_phone_number(cls, field: str | None) -> str | None:
        if field is None:
            return None
        return validators.parse_and_validate_mobile_number(field)


class UpdateTeacherAdmin(UpdateUserBase):
    type: Literal["teacher"] = "teacher"


class UpdateStudentAdmin(UpdateUserBase):
    type: Literal["student"] = "student"

    date_of_birth: date | None = None
    address: str | None = Field(min_length=15, max_length=100, default=None)

    @field_validator("date_of_birth", mode="after")
    @classmethod
    def validate_date_of_birth(cls, field: date | None) -> date | None:
        if field is None:
            return None

        return validators.validate_date_of_birth(field)


UpdateUserRequest = Annotated[
    UpdateTeacherAdmin | UpdateStudentAdmin,
    Field(discriminator="type"),
]


class UpdateUserCredentials(BaseModel):
    username: str | None = Field(min_length=6, max_length=20, default=None)
    email: EmailStr | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return validators.validate_username(v)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: EmailStr | None) -> str | None:
        if v is None:
            return None
        return v.strip().lower()


class SearchUserBase(BaseModel):
    firstname: str | None = Field(default=None, max_length=50)
    lastname: str | None = Field(default=None, max_length=50)
    middlename: str | None = Field(default=None, max_length=50)
    status: UserStatus | None = None


class SearchUserAdmin(SearchUserBase):
    username: str | None = Field(default=None, max_length=15)
    email: str | None = Field(default=None, max_length=20)
    phone_number: str | None = Field(default=None, max_length=16)
