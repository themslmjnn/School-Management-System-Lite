from sqlalchemy import String, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enum import Enum
from datetime import datetime

from db.database import Base


class SubjectLanguage(str, Enum):
    english = "english"
    french = "french"
    german = "german"
    arabic = "arabic"
    russian = "russian"
    tajik = "tajik"

class SubjectCategory(str, Enum):
    languages = "languages"
    mathematics = "mathematics"
    history = "history"
    science = "science"
    humanitarian = "humanitarian"
    sport = "sport"


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    language: Mapped[SubjectLanguage] = mapped_column(SQLEnum(SubjectLanguage), nullable=False)
    category: Mapped[SubjectCategory] = mapped_column(SQLEnum(SubjectCategory), nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student_subjects = relationship("StudentSubject", back_populates="subject")
    teacher_subjects = relationship("TeacherSubject", back_populates="subject")