from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from datetime import date, datetime

from src.models.student_model import StudentStatus
from src.schemas.user_schemas import UserSearchGeneral, UserSearchAdmin

class StudentBase(BaseModel):
    primary_info_id: int = Field(ge=1)

    grade: str
    enrolled_at: date


class StudentCreateGeneral(StudentBase):
    pass

class StudentCreateAdmin(StudentBase):
    status: StudentStatus


class StudentResponseBase(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)


class StudentResponseGeneral(StudentResponseBase):
    pass


class StudentResponseAdmin(StudentResponseBase):
    status: StudentStatus
    created_at: datetime
    updated_at: datetime


class StudentUpdateInfoAdmin(BaseModel):
    grade: Optional[str] = None
    enrolled_at: Optional[date] = None  
    status: Optional[StudentStatus] = None


class StudentSearchBase(BaseModel):
    grade: str


class StudentSearchGeneral(StudentSearchBase, UserSearchGeneral):
    pass


class StudentSearchAdmin(StudentSearchBase, UserSearchAdmin):
    pass