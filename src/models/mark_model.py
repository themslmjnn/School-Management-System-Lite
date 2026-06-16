from sqlalchemy import func, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enum import Enum
from datetime import datetime

from database import Base


class MarkType(str, Enum):
    regular_mark = "regular_mark"
    regular_exam = "regular_exam"
    midterm_exam = "midterm_exam"
    final_exam = "final_exam"


class Mark(Base):
    __tablename__ = "marks"

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)

    mark_type: Mapped[MarkType] = mapped_column(SQLEnum(MarkType), nullable=False, default=MarkType.regular_mark)

    mark: Mapped[int]

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student = relationship("Student", back_populates="student_marks")
    teacher = relationship("Teacher", back_populates="student_marks")