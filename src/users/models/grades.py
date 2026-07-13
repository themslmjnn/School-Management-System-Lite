import uuid

from sqlalchemy import UUID as PG_UUID
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Grade(Base):
    __tablename__ = "grades"

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[float] = mapped_column(nullable=False)

    student: Mapped["User"] = relationship("User", foreign_keys="[Grade.student_id]")  # noqa: F821


class GradeComment(Base):
    __tablename__ = "grade_comments"

    grade_id: Mapped[int] = mapped_column(
        ForeignKey("grades.id", ondelete="CASCADE"), nullable=False
    )

    # Live FK -- usable for joins/queries while the author's account still
    # exists. Set NULL on permanent deletion per the tracker decision;
    # NOT the source of truth for "who wrote this" once that happens.
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Permanent, immutable identity snapshot. NOT a foreign key -- deliberately
    # decoupled from the users table so it survives hard deletion untouched.
    # Captured once at comment-creation time and never updated afterward.
    author_public_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )

    # Frozen display-name snapshot, per the "frozen permanently" decision --
    # never refreshed even if the guardian's name changes while still active.
    author_display_name: Mapped[str] = mapped_column(String(101), nullable=False)

    content: Mapped[str] = mapped_column(String(1000), nullable=False)

    grade: Mapped["Grade"] = relationship(
        "Grade", foreign_keys="[GradeComment.grade_id]"
    )
    author: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys="[GradeComment.author_id]"
    )
