from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from src.utils.base_schema import BaseSchema


class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=10)
    academic_year: int = Field(ge=2000, le=2100)
    grade_level: int | None = None
    capacity: int | None = Field(gt=0, default=None)


class GroupUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=10)
    grade_level: int | None = None
    capacity: int | None = Field(gt=0, default=None)


class GroupResponse(BaseSchema):
    id: int
    name: str
    academic_year: int
    grade_level: int | None
    capacity: int | None
    is_archived: bool
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")


class SearchGroup(BaseModel):
    name: str | None = None
    academic_year: int | None = None
    include_archived: bool = False
