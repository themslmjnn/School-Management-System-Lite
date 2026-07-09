from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.users import User, UserActivation, UserLoginLockout, UserSession
from src.utils.enums import UserRole

ENTITY_TYPE = User | UserSession | UserActivation | UserLoginLockout


class UserRepositoryBase:
    @staticmethod
    def add_entity(db: AsyncSession, **new_entity: ENTITY_TYPE) -> None:
        for entity in new_entity.values():
            db.add(entity)

    @staticmethod
    async def count_users_with_contact(
        db: AsyncSession,
        role: UserRole | None,
        *,
        phone_number: str | None,
        email: str | None,
        exclude_user_id: int | None = None,
    ) -> int:
        role_filter = (
            User.role != UserRole.STUDENT if role is None else User.role == role
        )

        conditions = [role_filter]

        contact_conditions = []

        if phone_number is not None:
            contact_conditions.append(User.phone_number == phone_number)
        if email is not None:
            contact_conditions.append(User.email == email)

        conditions.append(or_(*contact_conditions))

        if exclude_user_id is not None:
            conditions.append(User.id != exclude_user_id)

        query = select(func.count(User.id)).where(*conditions)

        result = await db.execute(query)
        
        return result.scalar()