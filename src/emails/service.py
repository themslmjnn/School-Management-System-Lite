from sqlalchemy.ext.asyncio import AsyncSession

from src.core.pagination import PaginatedResponse
from src.emails.repository import PendingEmailRepository
from src.utils.base_constant import HTTP404
from src.utils.base_exception import PendingEmailNotFoundError
from src.utils.helpers import ensure_exists


class PendingEmailService:
    @staticmethod
    async def get_failed_emails(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 10,
    ) -> PaginatedResponse:
        failed_emails, total = await PendingEmailRepository.get_failed_emails(
            session,
            skip=skip,
            limit=limit,
        )

        return PaginatedResponse(
            items=failed_emails,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def retry_failed_email(
        session: AsyncSession,
        email_id: int,
    ) -> None:
        failed_email = await PendingEmailRepository.get_pending_email_by_id(
            session, email_id
        )
        ensure_exists(failed_email, PendingEmailNotFoundError(HTTP404.PENDING_EMAIL))

        await PendingEmailRepository.reset_for_retry(session, failed_email)

        await session.commit()
