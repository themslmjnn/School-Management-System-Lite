from sqlalchemy.ext.asyncio import AsyncSession

from src.core.pagination import PaginatedResponse
from src.emails.repository import PendingEmailRepository
from src.emails.schemas import SearchEmailAdmin
from src.utils.enums import EmailSortField, OrderBy


class PendingEmailService:
    @staticmethod
    async def get_emails(
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 10,
        filters: SearchEmailAdmin | None = None,
        sort_by: str = EmailSortField.CREATED_AT,
        order: str = OrderBy.DESC,
    ) -> PaginatedResponse:
        emails, total = await PendingEmailRepository.get_emails(
            session,
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            order=order,
        )

        return PaginatedResponse(
            items=emails,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )
