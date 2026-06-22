from pydantic import EmailStr
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models import User, UserActivation, UserSession
from src.utils.enums import UserRole


class UserRepositoryBase:
    @staticmethod
    def add_user(
        db: AsyncSession, new_user: User | UserSession | UserActivation
    ) -> None:
        db.add(new_user)

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: int,
        *,
        load_session: bool = False,
        load_activation: bool = False,
        allowed_roles: frozenset[UserRole] | None = None,
        excluded_roles: frozenset[UserRole] | None = None,
    ) -> User | None:
        query = select(User).filter(User.id == user_id)

        if allowed_roles:
            query = query.filter(User.role.in_(allowed_roles))
        if excluded_roles:
            query = query.filter(User.role.not_in(excluded_roles))
        if load_session:
            query = query.options(joinedload(User.session))
        if load_activation:
            query = query.options(joinedload(User.activation))

        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_student_with_identical_credentials(
        db: AsyncSession, phone_number: str, email: EmailStr
    ) -> int | None:
        query = select(func.count(User.id)).where(
            User.email == email,
            User.phone_number == phone_number,
            User.role == UserRole.STUDENT,
        )

        result = await db.execute(query)

        return result.scalar()

    @staticmethod
    async def get_parent_with_identical_credentials(
        db: AsyncSession, phone_number: str, email: EmailStr
    ) -> int | None:
        query = select(func.count(User.id)).where(
            and_(
                or_(
                    User.email == email,
                    User.phone_number == phone_number,
                ),
                User.role == UserRole.PARENT,
            )
        )

        result = await db.execute(query)

        return result.scalar()
