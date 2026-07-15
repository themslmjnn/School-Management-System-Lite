from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.academics.models import TeachingAssignment
from src.subjects.models import Subject
from src.subjects.schemas import SearchSubject
from src.utils.enums import OrderBy, SubjectSortField


class SubjectRepository:
    @staticmethod
    def add_subject(db: AsyncSession, new_subject: Subject) -> None:
        db.add(new_subject)

    @staticmethod
    async def get_subject_by_id(db: AsyncSession, subject_id: int) -> Subject | None:
        query = select(Subject).filter(Subject.id == subject_id)

        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_subject_by_code(db: AsyncSession, code: str) -> Subject | None:
        query = select(Subject).filter(Subject.code == code)

        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def paginate(
        db: AsyncSession, query: Select, skip: int, limit: int
    ) -> tuple[list, int]:
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await db.execute(query.offset(skip).limit(limit))

        return result.scalars().all(), total

    @staticmethod
    def apply_filters(base_query: Select, filters: SearchSubject | None) -> Select:
        if filters is None:
            return base_query

        if filters.name:
            base_query = base_query.filter(Subject.name.ilike(f"%{filters.name}%"))
        if filters.code:
            base_query = base_query.filter(Subject.code.ilike(f"%{filters.code}%"))
        if not filters.include_archived:
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
    async def get_subjects(
        db: AsyncSession,
        *,
        filters: SearchSubject | None = None,
        sort_by: str = SubjectSortField.CREATED_AT,
        order: str = OrderBy.DESC,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list["Subject"], int]:

        query = select(Subject)

        query = SubjectRepository.apply_filters(query, filters)
        query = SubjectRepository.apply_sorting(query, sort_by, order)

        return await SubjectRepository.paginate(db, query, skip, limit)

    @staticmethod
    async def has_active_teaching_assignments(
        db: AsyncSession, subject_id: int
    ) -> bool:
        query = select(func.count(TeachingAssignment.id)).filter(
            TeachingAssignment.subject_id == subject_id
        )

        result = await db.execute(query)

        return result.scalar() > 0
