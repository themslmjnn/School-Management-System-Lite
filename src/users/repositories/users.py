from datetime import UTC, datetime

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models.activation import UserActivation
from src.users.models.guardian_link import StudentGuardianLink
from src.users.models.login_lockout import UserLoginLockout
from src.users.models.session import UserSession
from src.users.models.user import User
from src.users.schemas.users import SearchUserAdmin, SearchUserBase
from src.utils.enums import (
    GuardianPriority,
    OrderBy,
    UserRole,
    UserSortField,
    UserStatus,
)

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
    def apply_base_filters(
        base_query: Select, filters: SearchUserBase | SearchUserAdmin | None
    ) -> Select:
        if filters is None:
            return base_query

        if filters.firstname:
            base_query = base_query.filter(
                User.firstname.ilike(f"%{filters.firstname}%")
            )
        if filters.lastname:
            base_query = base_query.filter(User.lastname.ilike(f"%{filters.lastname}%"))
        if filters.middlename:
            base_query = base_query.filter(
                User.middlename.ilike(f"%{filters.lastname}%")
            )
        if filters.status:
            base_query = base_query.filter(User.status == filters.status)
        if filters.allowed_roles:
            base_query = base_query.filter(User.role.in_(filters.allowed_roles))

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

    @staticmethod
    async def delete_user_if_due(db: AsyncSession, user_id: int) -> bool:
        query = delete(User).where(
            User.id == user_id,
            User.status == UserStatus.PENDING_DELETION,
            User.deletion_scheduled_for <= datetime.now(UTC),
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
                User.role == UserRole.GUARDIAN,
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

    @staticmethod
    async def get_user_by_id_pending_deletion(
        db: AsyncSession,
        user_id: int,
    ) -> User | None:
        query = select(User).where(
            User.id == user_id,
            User.role == UserRole.GUARDIAN,
            User.status == UserStatus.PENDING_DELETION,
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()


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
        base_query = select(User).filter(
            User.role.not_in({UserRole.SYSTEM_ADMIN, UserRole.DIRECTOR})
        )

        query = UserRepositoryAdmin._apply_admin_filters(base_query, filters)
        query = UserRepositoryBase.apply_sorting(query, sort_by, order)

        return await UserRepositoryBase.paginate(
            db=db,
            query=query,
            skip=skip,
            limit=limit,
        )


class GuardianLinkRepositoryAdmin:
    @staticmethod
    def add_link(db: AsyncSession, link: StudentGuardianLink) -> None:
        db.add(link)

    @staticmethod
    async def get_guardian_link(
        db: AsyncSession, parent_id: int, student_id: int
    ) -> StudentGuardianLink | None:
        query = select(StudentGuardianLink).where(
            StudentGuardianLink.guardian_id == parent_id,
            StudentGuardianLink.student_id == student_id,
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_guardian_link_by_priority(
        db: AsyncSession, student_id: int, priority: GuardianPriority
    ) -> StudentGuardianLink | None:
        query = select(StudentGuardianLink).where(
            StudentGuardianLink.student_id == student_id,
            StudentGuardianLink.priority == priority,
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()


class GuardianLinkRepositoryShared:
    @staticmethod
    async def get_children_for_guardian(
        db: AsyncSession, guardian_id: int
    ) -> list[StudentGuardianLink]:
        query = (
            select(StudentGuardianLink)
            .options(joinedload(StudentGuardianLink.student))
            .where(StudentGuardianLink.guardian_id == guardian_id)
        )

        result = await db.execute(query)

        return list(result.scalars().all())
