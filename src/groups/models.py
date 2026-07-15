from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Group(Base):
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    academic_year: Mapped[int] = mapped_column(nullable=False, index=True)
    grade_level: Mapped[int | None] = mapped_column(nullable=True)
    capacity: Mapped[int | None] = mapped_column(nullable=True)

    is_archived: Mapped[bool] = mapped_column(nullable=False, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("name", "academic_year", name="uix_group_name_academic_year"),
    )

    teaching_assignments: Mapped[list["TeachingAssignment"]] = relationship(  # noqa: F821
        "TeachingAssignment", back_populates="group"
    )
