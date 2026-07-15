from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class TeachingAssignment(Base):
    __tablename__ = "teaching_assignments"

    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "teacher_id", "subject_id", "group_id", name="uix_teaching_assignment"
        ),
    )

    teacher: Mapped["User"] = relationship("User")  # noqa: F821

    subject: Mapped["Subject"] = relationship(  # noqa: F821
        "Subject", back_populates="teaching_assignments"
    )

    group: Mapped["Group"] = relationship(  # noqa: F821
        "Group", back_populates="teaching_assignments"
    )
