from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.emails.models import PendingEmail
from src.emails.schemas import SearchEmailAdmin
from src.utils.enums import EmailSortField, OrderBy


class PendingEmailRepository:
    @staticmethod
    async def paginate(
        session: AsyncSession,
        *,
        query: Select,
        skip: int,
        limit: int,
    ) -> tuple[list[PendingEmail], int]:
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await session.execute(query.offset(skip).limit(limit))

        return result.scalars().all(), total

    @staticmethod
    def apply_filters(base_query: Select, filters: SearchEmailAdmin | None) -> Select:
        if filters is None:
            return base_query

        if filters.status is not None:
            base_query = base_query.filter(PendingEmail.status == filters.status)
        if filters.email_type is not None:
            base_query = base_query.filter(
                PendingEmail.email_type == filters.email_type
            )
        if filters.recipient_user_id is not None:
            base_query = base_query.filter(
                PendingEmail.recipient_user_id == filters.recipient_user_id
            )
        if filters.triggered_by is not None:
            base_query = base_query.filter(
                PendingEmail.triggered_by == filters.triggered_by
            )

        return base_query

    @staticmethod
    def apply_sorting(base_query: Select, sort_by: str, order: str) -> Select:
        if sort_by not in EmailSortField:
            sort_by = EmailSortField.CREATED_AT

        sort_column = getattr(PendingEmail, sort_by)

        if order == OrderBy.DESC:
            return base_query.order_by(sort_column.desc())

        return base_query.order_by(sort_column.asc())

    @staticmethod
    async def get_emails(
        session: AsyncSession,
        *,
        filters: SearchEmailAdmin | None = None,
        sort_by: str = EmailSortField.CREATED_AT,
        order: str = OrderBy.DESC,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[PendingEmail], int]:
        query = select(PendingEmail)

        query = PendingEmailRepository.apply_filters(query, filters)
        query = PendingEmailRepository.apply_sorting(query, sort_by, order)

        return await PendingEmailRepository.paginate(
            session, query=query, skip=skip, limit=limit
        )

    @staticmethod
    async def get_email_by_id(
        session: AsyncSession, email_id: int
    ) -> PendingEmail | None:
        query = select(PendingEmail).filter(PendingEmail.id == email_id)

        result = await session.execute(query)

        return result.scalar_one_or_none()
