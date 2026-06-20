from pydantic import BaseModel, Field

from typing import Optional
from datetime import datetime

from src.models.mark_model import MarkType
from src.schemas.base_schema import BaseSchema


class MarkBase(BaseModel):
    student_id: int = Field(ge=1)
    teacher_id: int = Field(ge=1)
    mark_type: MarkType
    mark: int = Field(ge=1)


class MarkCreateTeacher(MarkBase):
    pass


class MarkResponseBase(MarkBase, BaseSchema):
    pass


class MarkResponsePublic(MarkResponseBase):
    created_at: datetime
    updated_at: datetime


class MarkResponseAdmin(MarkResponseBase):
    id: int

    created_at: datetime
    updated_at: datetime


class MarkUpdateInfoAdmin(BaseModel):
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None
    mark_type: Optional[MarkType] = None
    mark: Optional[int] = None
