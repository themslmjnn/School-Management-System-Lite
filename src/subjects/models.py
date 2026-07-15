from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_archived: Mapped[bool] = mapped_column(nullable=False, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    teaching_assignments: Mapped[list["TeachingAssignment"]] = relationship(  # noqa: F821
        "TeachingAssignment", back_populates="subject"
    )
    enrollments: Mapped[list["StudentSubjectEnrollment"]] = relationship(  # noqa: F821
        "StudentSubjectEnrollment", back_populates="subject"
    )
