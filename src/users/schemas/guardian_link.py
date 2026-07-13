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


class UpdateGuardianPriority(BaseModel):
    priority: GuardianPriority


class ChildResponse(BaseSchema):
    id: int
    firstname: str
    lastname: str
    middlename: str | None
    priority: GuardianPriority
