from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from datetime import datetime

from src.models.subject_model import SubjectCategory, SubjectLanguage


class SubjectBase(BaseModel):
    title: str = Field(min_length=5, max_length=50)
    language: SubjectLanguage
    category: SubjectCategory


class SubjectCreateAdmin(SubjectBase):
    pass


class SubjectResponseBase(SubjectBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SubjectResponseGeneral(SubjectResponseBase):
    pass


class SubjectResponseAdmin(SubjectResponseBase):
    created_at: datetime
    updated_at: datetime


class SubjectUpdateInfoBaseAdmin(BaseModel):
    title: Optional[str] = Field(min_length=5, max_length=50, default=None)
    language: Optional[SubjectLanguage] = Field(default=None)
    category: Optional[SubjectCategory] = Field(default=None)


class SubjectSearchBase(BaseModel):
    title: Optional[str] = None
    language: Optional[SubjectLanguage] = None
    category: Optional[SubjectCategory] = None


class SubjectSearchGeneral(SubjectSearchBase):
    pass


class SubjectSearchAdmin(SubjectSearchBase):
    pass