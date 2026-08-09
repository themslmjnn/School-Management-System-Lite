from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base


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

    reset_password_token_hash: Mapped[str | None] = mapped_column(nullable=True)
    reset_password_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    pending_new_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email_change_code_hash: Mapped[str | None] = mapped_column(nullable=True)
    email_change_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="session")  # noqa: F821
