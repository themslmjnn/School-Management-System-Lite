from pydantic import BaseModel, Field

from typing import Optional
from datetime import date, datetime

from src.models.teacher_model import TeacherStatus
from src.models.association_models import TeacherSubjectStatus
from schemas.user import (
    UserCreateAdmin,
    UserResponseAdmin,
    UserResponsePublic,
)
from src.schemas.base_schema import BaseSchema


class TeacherBase1(BaseModel):
    hired_at: date


class TeacherBase2(TeacherBase1):
    status: TeacherStatus


class TeacherCreateAdmin(BaseModel):
    user: UserCreateAdmin
    teacher: TeacherBase1


class TeacherResponseBase(TeacherBase2, BaseSchema):
    id: int


class TeacherResponsePublic(BaseSchema):
    user: UserResponsePublic
    teacher: TeacherBase2


class TeacherResponseAdmin(BaseSchema):
    user: UserResponseAdmin
    teacher: TeacherResponseBase


class TeacherUpdateInfoAdmin(BaseModel):
    hired_at: Optional[date] = None
    status: Optional[TeacherStatus] = None


class TeacherSubjectBase(BaseModel):
    teacher_id: int = Field(ge=1)
    subject_id: int = Field(ge=1)


class TeacherSubjectCreateAdmin(TeacherSubjectBase):
    pass


class TeacherSubjectResponseAdmin(TeacherSubjectBase, BaseSchema):
    id: int

    status: TeacherSubjectStatus

    created_at: datetime
    updated_at: datetime


class TeacherSubjectUpdateInfoAdmin(BaseModel):
    teacher_id: Optional[int] = None
    subject_id: Optional[int] = None

    status: Optional[TeacherSubjectStatus] = None


class TeacherGroupBase(BaseModel):
    teacher_id: int = Field(ge=1)
    group_id: int = Field(ge=1)


class TeacherGroupCreateAdmin(TeacherGroupBase):
    pass


class TeacherGroupResponseAdmin(TeacherGroupBase, BaseSchema):
    id: int

    status: bool

    created_at: datetime
    updated_at: datetime


class TeacherGroupUpdateInfoAdmin(BaseModel):
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None

    status: Optional[bool] = None
