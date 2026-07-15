from datetime import datetime

from pydantic import BaseModel, field_serializer

from src.utils.base_schema import BaseSchema
from src.utils.enums import HeadOfClassRole


class TeachingAssignmentCreate(BaseModel):
    teacher_id: int
    subject_id: int
    group_id: int


class TeachingAssignmentResponse(BaseSchema):
    id: int
    teacher_id: int
    subject_id: int
    group_id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")


class HeadOfClassCreate(BaseModel):
    teacher_id: int
    role: HeadOfClassRole


class HeadOfClassResponse(BaseModel):
    id: int
    teacher_id: int
    group_id: int
    role: HeadOfClassRole
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")


class StudentSubjectEnrollmentResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    group_id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")
