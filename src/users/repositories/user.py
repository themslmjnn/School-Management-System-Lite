from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models.user import User
from src.users.schemas.system_admin import SearchUserAdmin, SearchUserBase
from src.utils.enums import (
    OrderBy,
    UserRole,
    UserSortField,
)


class UserRepositoryBase:
    @staticmethod
    async def count_users_with_contact(
        session: AsyncSession,
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

        result = await session.execute(query)

        return result.scalar()

    @staticmethod
    async def get_user_by_id(
        session: AsyncSession,
        user_id: int,
        *,
        load_session: bool = False,
        load_activation: bool = False,
        load_login_lockout: bool = False,
        load_group: bool = False,
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
        if load_group:
            query = query.options(joinedload(User.group))

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    def apply_base_filters(
        base_query: Select,
        filters: SearchUserBase | SearchUserAdmin | None,
        allowed_roles: frozenset[UserRole] | None = None,
    ) -> Select:
        if filters is not None:
            if filters.firstname:
                base_query = base_query.filter(
                    User.firstname.ilike(f"%{filters.firstname}%")
                )
            if filters.lastname:
                base_query = base_query.filter(
                    User.lastname.ilike(f"%{filters.lastname}%")
                )
            if filters.middlename:
                base_query = base_query.filter(
                    User.middlename.ilike(f"%{filters.middlename}%")
                )
            if filters.status:
                base_query = base_query.filter(User.status == filters.status)

        if allowed_roles:
            base_query = base_query.filter(User.role.in_(allowed_roles))

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
        session: AsyncSession,
        *,
        query: Select,
        skip: int,
        limit: int,
    ) -> tuple[list[User], int]:
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )

        total = count_result.scalar_one()

        result = await session.execute(query.offset(skip).limit(limit))

        return result.scalars().all(), total

    @staticmethod
    async def get_users(
        session: AsyncSession,
        *,
        excluded_roles: frozenset[UserRole] | None = None,
        allowed_roles: frozenset[UserRole] | None = None,
        filters: SearchUserBase | SearchUserAdmin | None = None,
        sort_by: str = UserSortField.CREATED_AT,
        order: str = OrderBy.DESC,
        skip: int = 0,
        limit: int = 10,
        group_id: int | None = None,
        load_group: bool = False,
    ) -> tuple[list[User], int]:
        base_query = select(User)

        if excluded_roles:
            base_query = base_query.filter(User.role.not_in(excluded_roles))
        if allowed_roles:
            base_query = base_query.filter(User.role.in_(allowed_roles))

        if group_id is not None:
            base_query = base_query.filter(User.group_id == group_id)
        if load_group:
            base_query = base_query.options(joinedload(User.group))

        query = UserRepositoryBase.apply_base_filters(base_query, filters)
        query = UserRepositoryBase.apply_sorting(query, sort_by, order)

        return await UserRepositoryBase.paginate(
            session, query=query, skip=skip, limit=limit
        )


class UserRepositoryAdmin:
    @staticmethod
    def _apply_admin_filters(
        base_query: Select,
        filters: SearchUserAdmin,
        allowed_roles: frozenset[UserRole] | None = None,
    ) -> Select:
        base_query = UserRepositoryBase.apply_base_filters(
            base_query, filters, allowed_roles
        )

        if filters.username:
            base_query = base_query.filter(User.username.ilike(f"%{filters.username}%"))
        if filters.email:
            base_query = base_query.filter(User.email.ilike(f"%{filters.email}%"))
        if filters.phone_number:
            base_query = base_query.filter(
                User.phone_number.ilike(f"%{filters.phone_number}%")
            )

        return base_query

    @staticmethod
    async def get_users_admin(
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 0,
        filters: SearchUserAdmin | None = None,
        sort_by: str = UserSortField.CREATED_AT,
        order: str = OrderBy.DESC,
        allowed_roles: frozenset[UserRole] | None = None,
        group_id: int | None = None,
        load_group: bool = False,
    ) -> tuple[list[User], int]:
        base_query = select(User).filter(
            User.role.not_in({UserRole.SYSTEM_ADMIN, UserRole.DIRECTOR})
        )

        if group_id is not None:
            base_query = base_query.filter(User.group_id == group_id)
        if load_group:
            base_query = base_query.options(joinedload(User.group))

        query = UserRepositoryAdmin._apply_admin_filters(
            base_query, filters, allowed_roles
        )
        query = UserRepositoryBase.apply_sorting(query, sort_by, order)

        return await UserRepositoryBase.paginate(
            session, query=query, skip=skip, limit=limit
        )
