from typing import Literal

from pydantic import EmailStr
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models import User, UserActivation, UserSession
from src.utils.enums import UserRole


class UserRepositoryBase:
    @staticmethod
    def add_entity(
        db: AsyncSession, new_entity: User | UserSession | UserActivation
    ) -> None:
        db.add(new_entity)

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
    async def count_users_with_contact(
        db: AsyncSession,
        role: UserRole,
        *,
        phone_number: str,
        email: EmailStr,
        match_mode: Literal["all", "any"] = "all",
    ) -> int:
        contact_filter = (
            and_(User.email == email, User.phone_number == phone_number)
            if match_mode == "all"
            else or_(User.email == email, User.phone_number == phone_number)
        )

        query = select(func.count(User.id)).where(
            User.role == role,
            contact_filter,
        )

        result = await db.execute(query)

        return result.scalar()
