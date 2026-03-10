from pydantic import BaseModel, Field

from typing import Optional
from datetime import date

from src.models.teacher_model import TeacherStatus
from src.schemas.user_schemas import UserCreateAdmin, UserResponseAdmin, UserResponsePublic
from src.schemas.base_schema import BaseSchema


class TeacherBase(BaseModel):
    hired_at: date
    status: TeacherStatus
    

class TeacherCreateAdmin(BaseModel):
    user: UserCreateAdmin
    teacher: TeacherBase


class TeacherResponseBase(TeacherBase, BaseSchema):
    id: int


class TeacherResponsePublic(BaseModel, BaseSchema):
    user: UserResponsePublic
    teacher: TeacherBase


class TeacherResponseAdmin(BaseModel, BaseSchema):
    id: int

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


class TeacherSubjectUpdateInfoAdmin(BaseModel):
    teacher_id: Optional[int] = None
    subject_id: Optional[int] = None


class TeacherGroupBase(BaseModel):
    student_id: int = Field(ge=1)
    subject_id: int = Field(ge=1)


class TeacherGroupCreateAdmin(TeacherSubjectBase):
    pass


class TeacherGroupResponseAdmin(TeacherSubjectBase, BaseSchema):
    id: int


class TeacherGroupUpdateInfoAdmin(BaseModel):
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None