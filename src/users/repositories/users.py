from pydantic import EmailStr
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models.users import User, UserActivation, UserLoginLockout, UserSession
from src.utils.enums import UserRole

ENTITY_TYPE = User | UserSession | UserActivation | UserLoginLockout


class UserRepositoryBase:
    @staticmethod
    def add_entity(db: AsyncSession, **new_entity: ENTITY_TYPE) -> None:
        for entity in new_entity.values():
            db.add(entity)

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
        role: UserRole | None,
        *,
        phone_number: str,
        email: EmailStr,
    ) -> int:
        role_filter = (
            User.role != UserRole.STUDENT if role is None else User.role == role
        )

        query = select(func.count(User.id)).where(
            role_filter,
            or_(
                User.email == email,
                User.phone_number == phone_number,
            ),
        )

        result = await db.execute(query)

        return result.scalar()
    
    @staticmethod
    async def get_parent(db: AsyncSession, target_user_id: int) -> User | None:
        query = (
            select(User)
            .where(
                and_(
                    User.id == target_user_id,
                    User.role == UserRole.PARENT,
                )
            )
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()
    
    @staticmethod
    def delete_user(db: AsyncSession, user_to_be_deleted: User) -> None:
        db.delete(user_to_be_deleted)

    # @staticmethod
    # async def delete_entity(db: AsyncSession, entity: ENTITY_TYPE) -> None:

