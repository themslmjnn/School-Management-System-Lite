from datetime import date, datetime

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from src.utils.enums import UserRole


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), index=True, nullable=False)

    date_of_birth: Mapped[date] = mapped_column(nullable=False)

    email: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(nullable=True)

    citizenship: Mapped[str] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(String(100), nullable=False)

    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    student_profile = relationship("Student", back_populates="user", uselist=False)

    session: Mapped["UserSession"] = relationship(
        "UserSession",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserSession(Base):
    __tablename__ = "users_sessions"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    access_token_version: Mapped[int] = mapped_column(nullable=False, default=1)

    refresh_token_hash: Mapped[str | None] = mapped_column(nullable=True)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refresh_token_family: Mapped[str | None] = mapped_column(String(64), nullable=True)

    failed_login_attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    reset_password_token_hash: Mapped[str | None] = mapped_column(nullable=True)
    reset_password_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    pending_new_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email_change_code_hash: Mapped[str | None] = mapped_column(nullable=True)
    email_change_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="session")