from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base
from src.utils.enums import GuardianPriority


class StudentGuardianLink(Base):
    __tablename__ = "student_guardian_links"

    guardian_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    priority: Mapped[GuardianPriority] = mapped_column(
        SQLEnum(GuardianPriority), nullable=False, default=GuardianPriority.SECONDARY
    )

    __table_args__ = (
        UniqueConstraint("guardian_id", "student_id", name="uix_guardian_student_pair"),
        Index(
            "uix_one_primary_guardian_per_student",
            "student_id",
            unique=True,
            postgresql_where=text("priority = 'PRIMARY'"),
        ),
        Index(
            "uix_one_secondary_guardian_per_student",
            "student_id",
            unique=True,
            postgresql_where=text("priority = 'SECONDARY'"),
        ),
    )

    guardian: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys="[StudentGuardianLink.guardian_id]"
    )

    student: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys="[StudentGuardianLink.student_id]"
    )
