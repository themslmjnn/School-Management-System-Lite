from pydantic import BaseModel, Field

from typing import Optional
from datetime import datetime


class MarkBase(BaseModel):
    student_id: int = Field(ge=1)
    teacher_id: int = Field(ge=1)
    mark: int = Field(ge=1)


class MarkCreateGeneral(MarkBase):
    pass


class MarkResponseBase(MarkBase):
    pass


class MarkResponseGeneral(MarkResponseBase):
    pass


class MarkResponseAdmin(MarkResponseBase):
    created_at: datetime
    updated_at: datetime