from sqlalchemy import ForeignKey, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enum import Enum
from datetime import date, datetime

from db.database import Base


class TeacherStatus(str, Enum):
    fired = "fired"
    dropped = "dropped"
    working = "working"


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)

    primary_info_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    hired_at: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[TeacherStatus] = mapped_column(SQLEnum(TeacherStatus), nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="teacher_profile")
    teacher_subjects = relationship("TeacherSubject", back_populates="teacher")
    teacher_groups = relationship("TeacherGroup", back_populates="teacher")
    student_marks = relationship("Mark", back_populates="teacher")