from pydantic import BaseModel, ConfigDict, Field

from typing import Optional
from datetime import date

from src.models.teacher_model import TeacherStatus
from src.schemas.user_schemas import UserCreateAdmin, UserResponseAdmin, UserResponsePublic


class TeacherBase(BaseModel):
    hired_at: date
    status: TeacherStatus
    

class TeacherCreateAdmin(BaseModel):
    user: UserCreateAdmin
    teacher: TeacherBase


class TeacherResponseBase(TeacherBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TeacherResponsePublic(BaseModel):
    user: UserResponsePublic
    teacher: TeacherBase

    model_config = ConfigDict(from_attributes=True)


class TeacherResponseAdmin(BaseModel):
    id: int

    user: UserResponseAdmin
    teacher: TeacherResponseBase

    model_config = ConfigDict(from_attributes=True)


class TeacherUpdateInfoAdmin(BaseModel):
    hired_at: Optional[date] = None
    status: Optional[TeacherStatus] = None


class TeacherSubjectBase(BaseModel):
    teacher_id: int = Field(ge=1)
    subject_id: int = Field(ge=1)


class TeacherSubjectCreateAdmin(TeacherSubjectBase):
    pass


class TeacherSubjectResponseAdmin(TeacherSubjectBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TeacherSubjectUpdateInfoAdmin(BaseModel):
    teacher_id: Optional[int] = None
    subject_id: Optional[int] = None


class TeacherGroupBase(BaseModel):
    student_id: int = Field(ge=1)
    subject_id: int = Field(ge=1)


class TeacherGroupCreateAdmin(TeacherSubjectBase):
    pass


class TeacherGroupResponseAdmin(TeacherSubjectBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TeacherGroupUpdateInfoAdmin(BaseModel):
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None