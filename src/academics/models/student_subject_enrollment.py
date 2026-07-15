from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class StudentSubjectEnrollment(Base):
    __tablename__ = "student_subject_enrollments"

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            "group_id",
            name="uix_student_subject_enrollment",
        ),
    )

    student: Mapped["User"] = relationship("User")  # noqa: F821

    subject: Mapped["Subject"] = relationship("Subject", back_populates="enrollments")  # noqa: F821

    group: Mapped["Group"] = relationship("Group", back_populates="enrollments")  # noqa: F821
