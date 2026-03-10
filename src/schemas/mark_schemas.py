from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from datetime import datetime


class MarkBase(BaseModel):
    student_id: int = Field(ge=1)
    teacher_id: int = Field(ge=1)
    mark: int = Field(ge=1)


class MarkCreateTeacher(MarkBase):
    pass


class MarkResponseBase(MarkBase):
    model_config = ConfigDict(from_attributes=True)


class MarkResponsePublic(MarkResponseBase):
    pass


class MarkResponseAdmin(MarkResponseBase):
    id: int

    created_at: datetime
    updated_at: datetime


class MarkUpdateInfoAdmin(BaseModel):
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None
    mark: Optional[int] = None