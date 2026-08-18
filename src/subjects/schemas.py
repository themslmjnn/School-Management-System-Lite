from datetime import datetime

from pydantic import BaseModel, Field, field_serializer, field_validator

from src.utils import validators as validators
from src.utils.base_schema import BaseSchema


class SubjectResponseAdmin(BaseModel):
    name: str
    code: str
    description: str | None


class SubjectResponseAdminCache(SubjectResponseAdmin, BaseSchema):
    id: int

    is_archived: bool
    archived_at: datetime | None

    created_at: datetime
    updated_at: datetime


class SubjectResponseAdminDetailed(SubjectResponseAdminCache):
    @field_serializer("archived_at")
    def serialize_archived_at(self, value: datetime | None) -> str | None:
        if value is None:
            return None

        return value.strftime("%d %b %Y, %H:%M")

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")


class SubjectCreate(BaseModel):
    name: str = Field(min_length=5, max_length=100)
    code: str = Field(min_length=3, max_length=20)
    description: str | None = Field(max_length=255, default=None)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return validators.normalize_subject_code(value)


class SubjectUpdate(BaseModel):
    name: str | None = Field(min_length=5, max_length=100, default=None)
    code: str | None = Field(min_length=3, max_length=20, default=None)
    description: str | None = Field(max_length=255, default=None)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        if value is None:
            return value

        return validators.normalize_subject_code(value)


class SearchSubject(BaseModel):
    name: str | None = None
    code: str | None = None
    include_archived: bool = False
