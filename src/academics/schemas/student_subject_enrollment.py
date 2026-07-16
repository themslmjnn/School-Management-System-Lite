from datetime import datetime

from pydantic import field_serializer

from src.utils.base_schema import BaseSchema


class StudentSubjectEnrollmentResponse(BaseSchema):
    id: int
    student_id: int
    subject_id: int
    group_id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")
