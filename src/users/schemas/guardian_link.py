from pydantic import BaseModel

from src.utils.base_schema import BaseSchema
from src.utils.enums import GuardianPriority


class CreateGuardianLink(BaseModel):
    guardian_id: int
    student_id: int
    priority: GuardianPriority = GuardianPriority.SECONDARY


class GuardianLinkResponse(BaseSchema):
    parent_id: int
    student_id: int
    priority: GuardianPriority
