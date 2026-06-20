from pydantic import BaseModel, Field

from typing import Optional
from datetime import date, datetime

from src.models.student_model import StudentStatus
from src.models.association_models import StudentSubjectStatus, StudentGroupStatus
from schemas.user import (
    UserCreateAdmin,
    UserResponseAdmin,
    UserResponsePublic,
    UserSearchPublic,
    UserSearchAdmin,
)
from src.schemas.base_schema import BaseSchema


class StudentBase1(BaseModel):
    grade: str
    enrolled_at: date


class StudentBase2(StudentBase1):
    status: StudentStatus


class StudentCreateAdmin(BaseModel):
    user: UserCreateAdmin
    student: StudentBase1


class StudentResponseBase(StudentBase2, BaseSchema):
    id: int


class StudentResponsePublic(BaseSchema):
    user: UserResponsePublic
    student: StudentBase2


class StudentResponseAdmin(BaseSchema):
    user: UserResponseAdmin
    student: StudentResponseBase


class StudentUpdateInfoAdmin(BaseModel):
    grade: Optional[str] = None
    enrolled_at: Optional[date] = None
    status: Optional[StudentStatus] = None


class StudentUpdateInfoResponseAdmin(StudentResponseBase):
    pass


class StudentSearchBase(StudentUpdateInfoAdmin):
    pass


class StudentSearchPublic(BaseModel):
    user: UserSearchPublic
    student: StudentSearchBase


class StudentSearchAdmin(BaseModel):
    user: UserSearchAdmin
    student: StudentSearchBase


class StudentSubjectBase(BaseModel):
    student_id: int = Field(ge=1)
    subject_id: int = Field(ge=1)


class StudentSubjectCreateAdmin(StudentSubjectBase):
    pass


class StudentSubjectResponseAdmin(StudentSubjectBase, BaseSchema):
    id: int

    status: StudentSubjectStatus

    created_at: datetime
    updated_at: datetime


class StudentSubjectUpdateInfoAdmin(BaseModel):
    student_id: Optional[int] = None
    subject_id: Optional[int] = None

    status: Optional[StudentSubjectStatus] = None


class StudentGroupBase(BaseModel):
    student_id: int = Field(ge=1)
    group_id: int = Field(ge=1)


class StudentGroupCreateAdmin(StudentGroupBase):
    pass


class StudentGroupResponseAdmin(StudentGroupBase, BaseSchema):
    id: int

    status: StudentGroupStatus

    created_at: datetime
    updated_at: datetime


class StudentGroupUpdateInfoAdmin(BaseModel):
    student_id: Optional[int] = None
    group_id: Optional[int] = None
