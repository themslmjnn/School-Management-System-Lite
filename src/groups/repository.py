from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# from src.academics.models.teaching_assignment import TeachingAssignment
from src.groups.models import Group
from src.groups.schemas import SearchGroup
from src.users.models.user import User
from src.utils.enums import GroupSortField, OrderBy, UserRole


class GroupRepository:
    @staticmethod
    def add_group(session: AsyncSession, new_group: Group) -> None:
        session.add(new_group)

    @staticmethod
    async def get_group_by_id(session: AsyncSession, group_id: int) -> Group | None:
        query = select(Group).filter(Group.id == group_id)

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_group_by_name_and_year(
        session: AsyncSession, name: str, academic_year: int
    ) -> Group | None:
        query = select(Group).filter(
            Group.name == name, Group.academic_year == academic_year
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def paginate(
        session: AsyncSession, query: Select, skip: int, limit: int
    ) -> tuple[list, int]:
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await session.execute(query.offset(skip).limit(limit))

        return result.scalars().all(), total

    @staticmethod
    def apply_filters(base_query: Select, filters: SearchGroup | None) -> Select:
        if filters is None:
            return base_query

        if filters.name:
            base_query = base_query.filter(Group.name.ilike(f"%{filters.name}%"))
        if filters.academic_year:
            base_query = base_query.filter(Group.academic_year == filters.academic_year)
        if not filters.include_archived:
            base_query = base_query.filter(Group.is_archived.is_(False))

        return base_query

    @staticmethod
    def apply_sorting(base_query: Select, sort_by: str, order: str) -> Select:
        if sort_by not in GroupSortField:
            sort_by = GroupSortField.CREATED_AT

        sort_column = getattr(Group, sort_by)

        if order == OrderBy.DESC:
            return base_query.order_by(sort_column.desc())

        return base_query.order_by(sort_column.asc())

    @staticmethod
    async def get_groups(
        session: AsyncSession,
        *,
        filters: SearchGroup | None = None,
        sort_by: str = GroupSortField.CREATED_AT,
        order: str = OrderBy.DESC,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Group], int]:

        query = select(Group)

        query = GroupRepository.apply_filters(query, filters)
        query = GroupRepository.apply_sorting(query, sort_by, order)

        return await GroupRepository.paginate(session, query, skip, limit)

    @staticmethod
    async def count_active_students(session: AsyncSession, group_id: int) -> int:
        query = select(func.count(User.id)).filter(
            User.group_id == group_id, User.role == UserRole.STUDENT
        )

        result = await session.execute(query)

        return result.scalar()

    @staticmethod
    async def has_active_students(session: AsyncSession, group_id: int) -> bool:
        return await GroupRepository.count_active_students(session, group_id) > 0

    # @staticmethod
    # async def has_active_teaching_assignments(session: AsyncSession, group_id: int) -> bool:
    #     query = select(func.count(TeachingAssignment.id)).filter(
    #         TeachingAssignment.group_id == group_id
    #     )

    #     result = await session.execute(query)

    #     return result.scalar() > 0

    @staticmethod
    async def get_students(
        session: AsyncSession, group_id: int, skip: int, limit: int
    ) -> tuple[list[User], int]:
        query = select(User).filter(
            User.group_id == group_id, User.role == UserRole.STUDENT
        )

        return await GroupRepository.paginate(session, query, skip, limit)
