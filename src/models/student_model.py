from sqlalchemy import ForeignKey, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enum import Enum
from datetime import date, datetime

from db.database import Base


class StudentStatus(str, Enum):
    dropped = "dropped"
    graduated = "graduated"
    enrolled = "enrolled"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)

    primary_info_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    grade: Mapped[str] = mapped_column(nullable=False)
    enrolled_at: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[StudentStatus] = mapped_column(SQLEnum(StudentStatus), nullable=False, default=StudentStatus.enrolled)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="student_profile")
    student_subjects = relationship("StudentSubject", back_populates="student")
    student_group = relationship("StudentGroup", back_populates="student")
    student_marks = relationship("Mark", back_populates="student")