from pydantic import BaseModel, Field

from typing import Optional
from datetime import datetime

from src.models.group_model import GroupLanguage

class GroupBase(BaseModel):
    title: str = Field(min_length=2, max_length=10)
    language: GroupLanguage


class GroupCreateAdmin(GroupBase):
    pass


class GroupResponseGeneral(GroupBase):
    pass


class GroupResponseAdmin(GroupBase):
    created_at: datetime
    updated_at: datetime


class GroupUpdateInfoAdmin(BaseModel):
    title: Optional[str] = Field(min_length=2, max_length=10, default=None)
    language: Optional[GroupLanguage] = Field(default=None)


class GroupSearchBase(BaseModel):
    title: Optional[str] = None
    language: Optional[GroupLanguage] = None


class GroupSearchGeneral(GroupSearchBase):
    pass


class GruopSearchAdmin(GroupSearchBase):
    created_at: Optional[datetime] = None