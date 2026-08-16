import uuid
from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base
from src.utils.enums import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    public_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
        index=True,
    )

    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    firstname: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    lastname: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    middlename: Mapped[str | None] = mapped_column(String(50), nullable=True)

    date_of_birth: Mapped[date | None] = mapped_column(nullable=True)
    address: Mapped[str | None] = mapped_column(String(100), nullable=True)

    phone_number: Mapped[str] = mapped_column(String(25), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False)

    password_hash: Mapped[str | None] = mapped_column(nullable=True)

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), nullable=False, default=UserRole.STUDENT
    )
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus), nullable=False, default=UserStatus.PENDING_ACTIVATION
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=False)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"), nullable=True, index=True
    )

    __table_args__ = (
        Index(
            "uix_non_student_unique_phone",
            "phone_number",
            unique=True,
            postgresql_where=text("role <> 'STUDENT'"),
        ),
        Index(
            "uix_non_student_unique_email",
            "email",
            unique=True,
            postgresql_where=text("role <> 'STUDENT'"),
        ),
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

    session: Mapped["UserSession"] = relationship(  # noqa: F821
        "UserSession",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    login_lockout: Mapped["UserLoginLockout"] = relationship(  # noqa: F821
        "UserLoginLockout",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    activation: Mapped["UserActivation"] = relationship(  # noqa: F821
        "UserActivation",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    group: Mapped["Group"] = relationship("Group", back_populates="students")  # noqa: F821
