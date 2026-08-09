from datetime import date, datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    computed_field,
    field_serializer,
    field_validator,
)

from src.groups.schemas import GroupResponseBase
from src.users.schemas.system_admin.user import UserCacheSchema, UserResponseAdmin
from src.utils import validators as validators
from src.utils.base_schema import BaseSchema


class StudentResponseAdmin(UserResponseAdmin):
    group: GroupResponseBase | None = None


class StudentCacheSchema(UserCacheSchema):
    group: GroupResponseBase | None = None


class StudentResponseAdminDetailed(StudentCacheSchema):
    phone_number: str = Field(exclude=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")

    @computed_field
    @property
    def format_phone_number(self) -> str:
        return validators.format_phone_for_display(self.phone_number)


class UserResponseSelf(BaseSchema):
    id: int
    username: str
    firstname: str
    lastname: str
    middlename: str | None
    date_of_birth: date | None
    phone_number: str = Field(exclude=True)
    email: str
    address: str | None
    created_at: datetime

    @field_serializer("created_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")

    @computed_field
    @property
    def format_phone_number(self) -> str:
        return validators.format_phone_for_display(self.phone_number)


class UpdateMeProfile(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    middlename: str | None = None
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


class UpdateMeCredentials(BaseModel):
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


class ConfirmEmailChange(BaseModel):
    code: str


class UpdateMePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validators.validate_password(v)


class UserSelfCacheSchema(BaseSchema):
    id: int
    username: str
    firstname: str
    lastname: str
    middlename: str | None
    date_of_birth: date | None
    phone_number: str
    email: str
    address: str | None
    created_at: datetime


class StudentSelfCacheSchema(UserSelfCacheSchema):
    group: GroupResponseBase | None = None


class StudentResponseSelf(UserResponseSelf):
    group: GroupResponseBase | None = None
