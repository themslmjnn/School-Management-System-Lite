from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import CurrentUser
from src.emails.exceptions.constants import HTTP404
from src.emails.exceptions.exceptions import PendingEmailNotFoundError
from src.emails.repository import PendingEmailRepository
from src.pagination import PaginatedResponse
from src.utils.base_constant import HTTP403
from src.utils.base_exception import AccessDeniedError
from src.utils.enums import UserRole
from src.utils.helpers import ensure_exists


class PendingEmailService:
    @staticmethod
    async def get_failed_emails(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
    ) -> PaginatedResponse:
        failed_emails, total = await PendingEmailRepository.get_failed_emails(
            db,
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
        db: AsyncSession,
        email_id: int,
    ) -> None:
        failed_email = await PendingEmailRepository.get_pending_email_by_id(
            db, email_id
        )
        ensure_exists(failed_email, PendingEmailNotFoundError(HTTP404.PENDING_EMAIL))

        await PendingEmailRepository.reset_for_retry(db, failed_email)

    @staticmethod
    async def get_my_failed_emails(
        db: AsyncSession,
        current_user_id: int,
        skip: int = 0,
        limit: int = 10,
    ) -> PaginatedResponse:
        failed_emails, total = await PendingEmailRepository.get_failed_by_triggered_by(
            db,
            triggered_by=current_user_id,
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
    async def retry_my_failed_email(
        db: AsyncSession,
        current_user: CurrentUser,
        email_id: int,
    ) -> None:
        failed_email = await PendingEmailRepository.get_pending_email_by_id(
            db, email_id
        )
        ensure_exists(failed_email, PendingEmailNotFoundError(HTTP404.PENDING_EMAIL))

        if (
            current_user.role != UserRole.system_admin
            and failed_email.triggered_by != current_user.id
        ):
            raise AccessDeniedError(HTTP403.ACCESS_DENIED)

        await PendingEmailRepository.reset_for_retry(db, failed_email)
