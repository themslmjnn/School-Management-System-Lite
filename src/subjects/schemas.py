from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from src.utils.base_schema import BaseSchema


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=20)
    description: str | None = Field(max_length=255, default=None)


class SubjectUpdate(BaseModel):
    name: str | None = Field(min_length=1, max_length=100, default=None)
    code: str | None = Field(min_length=1, max_length=20, default=None)
    description: str | None = Field(max_length=255, default=None)


class SubjectResponse(BaseSchema):
    id: int
    name: str
    code: str
    description: str | None
    is_archived: bool
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")