from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.utils.enums import HeadOfClassRole


class HeadOfClassAssignment(Base):
    __tablename__ = "head_of_class_assignments"

    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    role: Mapped[HeadOfClassRole] = mapped_column(
        SQLEnum(HeadOfClassRole), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("group_id", "role", name="uix_head_of_class_role_per_group"),
        UniqueConstraint(
            "teacher_id", "group_id", name="uix_head_of_class_teacher_per_group"
        ),
    )

    teacher: Mapped["User"] = relationship("User")  # noqa: F821

    group: Mapped["Group"] = relationship(  # noqa: F821
        "Group", back_populates="head_of_class_assignments"
    )
