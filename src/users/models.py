from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
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

    session: Mapped["UserSession"] = relationship(
        "UserSession",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    activation: Mapped["UserActivation"] = relationship(
        "UserActivation",
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


class UserActivation(Base):
    __tablename__ = "users_activations"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    invite_token_hash: Mapped[str | None] = mapped_column(nullable=True)
    invite_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="activation")
