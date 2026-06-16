from datetime import date

from sqlalchemy import Enum as SQLEnum
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