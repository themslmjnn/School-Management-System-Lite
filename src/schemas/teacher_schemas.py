from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from datetime import date, datetime

from src.models.teacher_model import TeacherStatus

class TeacherBase(BaseModel):
    primary_info_id: int = Field(ge=1)

    hired_at: date


class TeacherCreateGeneral(TeacherBase):
    pass

class TeacherCreateAdmin(TeacherBase):
    status: TeacherStatus


class TeacherResponseBase(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TeacherResponseGeneral(TeacherResponseBase):
    pass


class TeacherResponseAdmin(TeacherResponseBase):
    status: TeacherStatus
    created_at: datetime
    updated_at: datetime


class TeacherUpdateInfoBase(BaseModel):
    hired_at: Optional[date] = None
    status: Optional[TeacherStatus] = None