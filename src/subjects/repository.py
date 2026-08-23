from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.subjects.models import Subject
from src.subjects.schemas import SearchSubjectAdmin
from src.utils.enums import OrderBy, SubjectSortField


class SubjectRepository:
    @staticmethod
    def apply_filters(base_query: Select, filters: SearchSubjectAdmin | None) -> Select:
        if filters is None:
            return base_query

        if filters.name:
            base_query = base_query.filter(Subject.name.ilike(f"%{filters.name}%"))
        if filters.code:
            base_query = base_query.filter(Subject.code.ilike(f"%{filters.code}%"))
        if not getattr(filters, "include_archived", False):
            base_query = base_query.filter(Subject.is_archived.is_(False))

        return base_query

    @staticmethod
    def apply_sorting(base_query: Select, sort_by: str, order: str) -> Select:
        if sort_by not in SubjectSortField:
            sort_by = SubjectSortField.CREATED_AT

        sort_column = getattr(Subject, sort_by)

        if order == OrderBy.DESC:
            return base_query.order_by(sort_column.desc())

        return base_query.order_by(sort_column.asc())

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
    async def get_subjects(
        session: AsyncSession,
        *,
        filters: SearchSubjectAdmin | None = None,
        sort_by: str = SubjectSortField.CREATED_AT,
        order: str = OrderBy.DESC,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list["Subject"], int]:

        query = select(Subject)

        query = SubjectRepository.apply_filters(query, filters)
        query = SubjectRepository.apply_sorting(query, sort_by, order)

        return await SubjectRepository.paginate(session, query, skip, limit)

    @staticmethod
    async def get_subject_by_id(
        session: AsyncSession, subject_id: int
    ) -> Subject | None:
        query = select(Subject).filter(Subject.id == subject_id)

        result = await session.execute(query)

        return result.scalar_one_or_none()
