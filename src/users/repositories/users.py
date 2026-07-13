from datetime import datetime, UTC

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models.users import User, UserActivation, UserLoginLockout, UserSession
from src.utils.enums import UserRole, UserStatus

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

        contact_condition = (
            User.phone_number == phone_number
            if phone_number is not None
            else User.email == email
        )

        conditions = [role_filter, contact_condition]

        if exclude_user_id is not None:
            conditions.append(User.id != exclude_user_id)

        query = select(func.count(User.id)).where(*conditions)

        result = await db.execute(query)

        return result.scalar()

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: int,
        *,
        load_session: bool = False,
        load_activation: bool = False,
        load_login_lockout: bool = False,
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
        if load_login_lockout:
            query = query.options(joinedload(User.login_lockout))

        result = await db.execute(query)

        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_user_if_due(db: AsyncSession, user_id: int) -> bool:
        query = (
                delete(User)
                .where(
                    User.id == user_id,
                    User.status == UserStatus.PENDING_DELETION,
                    User.deletion_scheduled_for <= datetime.now(UTC),
                )
            )
        
        result = await db.execute(query)

        return result.rowcount > 0


    @staticmethod
    async def get_user_ids_due_for_hard_deletion(db: AsyncSession) -> list[int]:
        query = select(User.id).where(
            User.status == UserStatus.PENDING_DELETION,
            User.deletion_scheduled_for <= datetime.now(UTC),
        )

        result = await db.execute(query)

        return list(result.scalars().all())


    @staticmethod
    async def reactivate_pending_deletion_user(db: AsyncSession, user_id: int) -> bool:
        query = (
            update(User)
            .where(
                User.id == user_id,
                User.role == UserRole.PARENT,
                User.status == UserStatus.PENDING_DELETION,
            )
            .values(
                status=UserStatus.ACTIVE,
                is_active=True,
                deletion_scheduled_for=None,
            )
        )

        result = await db.execute(query)
        
        return result.rowcount > 0
