from datetime import UTC, datetime

from pydantic import EmailStr
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models.users import User, UserActivation, UserLoginLockout, UserSession
from src.users.schemas.users import SearchStudentAdmin, SearchUserAdmin, SearchUserBase
from src.utils.enums import OrderBy, UserRole, UserSortField, UserStatus

ENTITY_TYPE = User | UserSession | UserActivation | UserLoginLockout


class UserRepositoryBase:
    @staticmethod
    def add_entity(db: AsyncSession, **new_entity: ENTITY_TYPE) -> None:
        for entity in new_entity.values():
            db.add(entity)

    @staticmethod
    def apply_base_filters(
        base_query: Select, filters: SearchUserBase | SearchUserAdmin | None
    ) -> Select:
        if filters is None:
            return base_query

        if filters.first_name:
            base_query = base_query.filter(
                User.first_name.ilike(f"%{filters.first_name}%")
            )
        if filters.last_name:
            base_query = base_query.filter(
                User.last_name.ilike(f"%{filters.last_name}%")
            )
        

        return base_query

    @staticmethod
    def apply_sorting(base_query: Select, sort_by: str, order: str) -> Select:
        if sort_by not in UserSortField:
            sort_by = UserSortField.CREATED_AT

        sort_column = getattr(User, sort_by)

        if order == OrderBy.DESC:
            return base_query.order_by(sort_column.desc())

        return base_query.order_by(sort_column.asc())

    @staticmethod
    async def paginate(
        db: AsyncSession,
        query: Select,
        skip: int,
        limit: int,
    ) -> tuple[list[User], int]:

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )

        total = count_result.scalar_one()

        result = await db.execute(query.offset(skip).limit(limit))

        return result.scalars().all(), total

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
    async def delete_user(db: AsyncSession, user_to_be_deleted: User) -> None:
        await db.delete(user_to_be_deleted)

    @staticmethod
    async def get_users_due_for_hard_deletion(
        db: AsyncSession,
    ) -> list[User]:
        query = select(User).where(
            User.status == UserStatus.PENDING_DELETION,
            User.deletion_scheduled_for <= datetime.now(UTC),
        )

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def get_user_by_id_pending_deletion(
        db: AsyncSession,
        user_id: int,
    ) -> User | None:
        query = select(User).where(
            User.id == user_id,
            User.role == UserRole.PARENT,
            User.status == UserStatus.PENDING_DELETION,
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_users(
        db: AsyncSession,
        *,
        excluded_roles: frozenset[UserRole] | None = None,
        allowed_roles: frozenset[UserRole] | None = None,
        filters: SearchUserBase | SearchUserAdmin | None = None,
        sort_by: str = UserSortField.CREATED_AT,
        order: str = OrderBy.DESC,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[User], int]:
        query = select(User)

        if excluded_roles:
            query = query.filter(User.role.not_in(excluded_roles))
        if allowed_roles:
            query = query.filter(User.role.in_(allowed_roles))

        query = UserRepositoryBase.apply_base_filters(query, filters)
        query = UserRepositoryBase.apply_sorting(query, sort_by, order)

        return await UserRepositoryBase.paginate(db, query, skip, limit)



class UserRepositoryAdmin:
    @staticmethod
    def _apply_admin_filters(base_query, filters: SearchUserAdmin) -> Select:
        base_query = UserRepositoryBase.apply_base_filters(base_query, filters)

        if filters.username:
            base_query = base_query.filter(User.username.ilike(f"%{filters.username}%"))
        if filters.email:
            base_query = base_query.filter(User.email.ilike(f"%{filters.email}%"))
        if filters.phone_number:
            base_query = base_query.filter(
                User.phone_number.ilike(f"%{filters.phone_number}%")
            )
        if filters.role:
            base_query = base_query.filter(User.role == filters.role)
        if filters.is_active is not None:
            base_query = base_query.filter(User.is_active == filters.is_active)

        return base_query

    @staticmethod
    async def get_users_admin(
        db: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchUserAdmin | None = None,
        sort_by: str = UserSortField.CREATED_AT,
        order: str = OrderBy.DESC,
    ) -> tuple[list[User], int]:
        base_query = select(User).filter(User.role != UserRole.SYSTEM_ADMIN)

        query = UserRepositoryAdmin._apply_admin_filters(base_query, filters)
        query = UserRepositoryBase.apply_sorting(query, sort_by, order)

        return await UserRepositoryBase.paginate(
            db=db,
            query=query,
            skip=skip,
            limit=limit,
        )