from datetime import date

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.utils.enums import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    firstname: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    lastname: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    middlename: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(nullable=False)
    phone_number: Mapped[str] = mapped_column(String(25), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), nullable=False, default=UserRole.STUDENT
    )
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint("phone_number", "email", "role", name="uix_parent_fields"),
    )

    creator: Mapped["User"] = relationship(
        "User",
        remote_side="User.id",
        foreign_keys="[User.created_by]",
        back_populates="created_users",
    )

    created_users: Mapped[list["User"]] = relationship(
        "User", foreign_keys="[User.created_by]", back_populates="creator"
    )
