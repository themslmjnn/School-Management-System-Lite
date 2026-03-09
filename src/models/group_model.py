from sqlalchemy import String, func, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enum import Enum
from datetime import datetime

from db.database import Base


class GroupLanguage(str, Enum):
    english = "english"
    russian = "russian"
    tajik = "tajik"


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    language: Mapped[GroupLanguage] = mapped_column(SQLEnum(GroupLanguage), nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student_group = relationship("StudentGroup", back_populates="group", uselist=False)
    teacher_groups = relationship("TeacherGroup",  back_populates="group")

    __table_args__ = (
        UniqueConstraint('title', 'language', name='uix_title_language_group'),
    )