
from sqlalchemy import ForeignKey, func, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enum import Enum
from datetime import datetime

from db.database import Base


# class StudentSubjectStatus(str, Enum):
#     finished= "finished"
#     withdrawn = "withdrawn"
#     studying = "studying"


class StudentSubject(Base):
    __tablename__ = "student_subject"

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)

    # status: Mapped[StudentSubjectStatus] = mapped_column(SQLEnum(StudentSubjectStatus), nullable=False, default=StudentSubjectStatus.studying)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student = relationship("Student", back_populates="student_subjects")
    subject = relationship("Subject", back_populates="student_subjects")


    # __table_args__ = (
    #     UniqueConstraint("student_id", "subject_id", "status", name="uix_student_subject"),
    # )


class StudentGroup(Base):
    __tablename__ = "student_group"

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="student_group")
    group = relationship("Group", back_populates="student_group")


class TeacherSubject(Base):
    __tablename__ = "teacher_subject"

    id: Mapped[int] = mapped_column(primary_key=True)

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    teacher = relationship("Teacher", back_populates="teacher_subjects")
    subject = relationship("Subject", back_populates="teacher_subjects")


class TeacherGroup(Base):
    __tablename__ = "teacher_group"

    id: Mapped[int] = mapped_column(primary_key=True)

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    teacher = relationship("Teacher", back_populates="teacher_groups")
    group = relationship("Group", back_populates="teacher_groups")