from datetime import datetime

from pydantic import Field, computed_field, field_serializer

from src.groups.schemas import GroupResponseBase
from src.users.schemas.system_admin.user import UserCacheSchema, UserResponseAdmin
from src.utils import validators as validators


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
