from datetime import datetime

from pydantic import BaseModel, field_serializer

from src.utils.base_schema import BaseSchema
from src.utils.enums import GuardianPriority


class CreateGuardianLinkAdmin(BaseModel):
    guardian_id: int
    student_id: int
    priority: GuardianPriority = GuardianPriority.SECONDARY


class GuardianLinkResponse(BaseSchema):
    id: int
    guardian_fullname: str
    student_fullname: str
    student_grade_level: int | None
    priority: GuardianPriority


class GuardianLinkResponseAdmin(GuardianLinkResponse):
    guardian_id: int
    student_id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%d %b %Y, %H:%M")
