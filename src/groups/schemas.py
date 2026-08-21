from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from src.utils.base_schema import BaseSchema


class GroupResponseBase(BaseSchema):
    name: str
    academic_year: int
    grade_level: int | None
    capacity: int | None


class GroupResponseAdminCache(GroupResponseBase, BaseSchema):
    id: int

    is_archived: bool
    archived_at: datetime | None

    created_at: datetime
    updated_at: datetime


class GroupResponseAdminDetailed(GroupResponseAdminCache):
    @field_serializer("archived_at")
    def serialize_archived_at(self, value: datetime | None) -> str | None:
        if value is None:
            return None

        return value.strftime("%d %b %Y, %H:%M")

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")


class GroupResponseDirectorCache(GroupResponseBase, BaseSchema):
    id: int

    is_archived: bool

    created_at: datetime


class GroupResponseDirectorDetailed(GroupResponseDirectorCache):
    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")


class CreateGroupAdmin(BaseModel):
    name: str = Field(min_length=2, max_length=10)
    academic_year: int = Field(ge=2000, le=2100)
    grade_level: int | None = None
    capacity: int | None = Field(gt=0, default=None)


class UpdateGroupAdmin(BaseModel):
    name: str | None = Field(min_length=2, max_length=10, default=None)
    grade_level: int | None = None
    capacity: int | None = Field(gt=0, default=None)


class SearchGroupBase(BaseModel):
    name: str | None = None
    academic_year: int | None = None


class SearchGroupAdmin(SearchGroupBase):
    include_archived: bool = False
