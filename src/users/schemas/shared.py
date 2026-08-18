from datetime import date, datetime

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_serializer,
    field_validator,
)

from src.groups.schemas import GroupResponseBase
from src.utils import validators as validators
from src.utils.base_schema import BaseSchema


class UserResponseSelfCache(BaseSchema):
    id: int

    username: str

    firstname: str
    lastname: str
    middlename: str | None

    phone_number: str
    email: str

    date_of_birth: date | None
    address: str | None

    created_at: datetime


class UserResponseSelf(UserResponseSelfCache):
    phone_number: str = Field(exclude=True)

    @field_serializer("created_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")

    @computed_field
    @property
    def format_phone_number(self) -> str:
        return validators.format_phone_for_display(self.phone_number)


class StudentResponseSelfCache(UserResponseSelfCache):
    group: GroupResponseBase | None = None


class StudentResponseSelf(StudentResponseSelfCache):
    phone_number: str = Field(exclude=True)

    @field_serializer("created_at")
    def serialize_datetimes(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")

    @computed_field
    @property
    def format_phone_number(self) -> str:
        return validators.format_phone_for_display(self.phone_number)


class ConfirmEmailChange(BaseModel):
    code: str


class UpdateMePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validators.validate_password(v)
