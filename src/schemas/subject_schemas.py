from pydantic import BaseModel, Field

from typing import Optional
from datetime import datetime

from src.models.subject_model import SubjectCategory, SubjectLanguage
from src.schemas.base_schema import BaseSchema


class SubjectBase(BaseModel):
    title: str = Field(min_length=5, max_length=50)
    language: SubjectLanguage
    category: SubjectCategory


class SubjectCreateAdmin(SubjectBase):
    pass


class SubjectResponsePublic(SubjectBase, BaseSchema):
    pass


class SubjectResponseAdmin(SubjectBase, BaseSchema):
    id: int

    created_at: datetime
    updated_at: datetime


class SubjectUpdateInfoAdmin(BaseModel):
    title: Optional[str] = Field(min_length=5, max_length=50, default=None)
    language: Optional[SubjectLanguage] = Field(default=None)
    category: Optional[SubjectCategory] = Field(default=None)


class SubjectSearchBase(BaseModel):
    title: Optional[str] = None
    language: Optional[SubjectLanguage] = None
    category: Optional[SubjectCategory] = None


class SubjectSearchPublic(SubjectSearchBase):
    pass


class SubjectSearchAdmin(SubjectSearchBase):
    pass