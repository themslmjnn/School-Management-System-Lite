from datetime import date, datetime

from pydantic import (
    Field,
    computed_field,
    field_serializer,
)

from src.groups.schemas import GroupResponseBase
from src.users.utils.shared_schemas import UserResponseBase
from src.utils import validators
from src.utils.base_schema import BaseSchema
from src.utils.enums import UserRole, UserStatus


class UserResponseDirectorCache(UserResponseBase, BaseSchema):
    id: int

    phone_number: str

    date_of_birth: date | None
    address: str | None

    role: UserRole
    status: UserStatus

    created_at: datetime


class UserResponseDirectorDetailed(UserResponseDirectorCache):
    phone_number: str = Field(exclude=True)

    @field_serializer("created_at")
    def serialize_datetimes(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")

    @computed_field
    @property
    def format_phone_number(self) -> str:
        return validators.format_phone_for_display(self.phone_number)


class StudentResponseDirector(UserResponseBase):
    group: GroupResponseBase | None = None


class StudentResponseDirectorCache(UserResponseDirectorCache):
    group: GroupResponseBase | None = None


class StudentResponseDirectorDetailed(StudentResponseDirectorCache):
    phone_number: str = Field(exclude=True)

    @field_serializer("created_at")
    def serialize_datetimes(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")

    @computed_field
    @property
    def format_phone_number(self) -> str:
        return validators.format_phone_for_display(self.phone_number)
