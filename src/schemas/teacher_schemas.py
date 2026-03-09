from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from datetime import date, datetime

from src.models.teacher_model import TeacherStatus
from src.schemas.user_schemas import UserCreateAdmin, UserResponseAdmin, UserResponseGeneral

class TeacherBase(BaseModel):
    hired_at: date
    status: TeacherStatus
    

class TeacherCreateAdmin(BaseModel):
    teacher_primary_data: UserCreateAdmin
    teacher_advanced_data: TeacherBase


class TeacherResponseBase(TeacherBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TeacherResponseGeneral(BaseModel):
    teacher_primary_data: UserResponseGeneral
    teacher_advanced_data: TeacherBase

    model_config = ConfigDict(from_attributes=True)


class TeacherResponseAdmin(BaseModel):
    teacher_primary_data: UserResponseAdmin
    teacher_advanced_data: TeacherResponseBase

    model_config = ConfigDict(from_attributes=True)


class TeacherUpdateInfoBase(BaseModel):
    hired_at: Optional[date] = None
    status: Optional[TeacherStatus] = None