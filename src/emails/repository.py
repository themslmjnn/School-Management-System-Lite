from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.emails.models import PendingEmail
from src.utils.enums import EmailSendingStatus


class PendingEmailRepository:
    @staticmethod
    async def _count_failed(session: AsyncSession) -> int:
        query = select(func.count()).select_from(
            select(PendingEmail)
            .where(PendingEmail.status == EmailSendingStatus.FAILED)
            .subquery()
        )

        result = await session.execute(query)

        return result.scalar_one()

    @staticmethod
    async def get_pending_emails(
        session: AsyncSession, limit: int = 10
    ) -> list[PendingEmail]:
        query = (
            select(PendingEmail)
            .where(
                PendingEmail.status == EmailSendingStatus.PENDING,
                PendingEmail.retry_count < 3,
            )
            .order_by(PendingEmail.created_at.asc())
            .limit(limit)
        )

        result = await session.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def get_failed_emails(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[PendingEmail], int]:
        total = await PendingEmailRepository._count_failed(session)

        query = (
            select(PendingEmail)
            .where(PendingEmail.status == EmailSendingStatus.FAILED)
            .order_by(PendingEmail.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(query)

        return list(result.scalars().all()), total

    @staticmethod
    async def get_failed_by_triggered_by(
        session: AsyncSession,
        triggered_by: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[PendingEmail], int]:
        count_query = select(func.count()).select_from(
            select(PendingEmail)
            .where(
                PendingEmail.status == EmailSendingStatus.FAILED,
                PendingEmail.triggered_by == triggered_by,
            )
            .subquery()
        )
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        query = (
            select(PendingEmail)
            .where(
                PendingEmail.status == EmailSendingStatus.FAILED,
                PendingEmail.triggered_by == triggered_by,
            )
            .order_by(PendingEmail.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)

        return list(result.scalars().all()), total

    @staticmethod
    async def get_pending_email_by_id(
        session: AsyncSession, email_id: int
    ) -> PendingEmail | None:
        query = select(PendingEmail).filter(PendingEmail.id == email_id)

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_pending_email_by_triggered_by(
        session: AsyncSession, triggered_by: int | None
    ) -> list[PendingEmail]:
        query = select(PendingEmail).filter(PendingEmail.triggered_by == triggered_by)

        result = await session.execute(query)

        return result.scalars().all()

    @staticmethod
    async def mark_sent(record: PendingEmail) -> None:
        record.status = EmailSendingStatus.SENT
        record.sent_at = datetime.now(UTC)

    @staticmethod
    async def mark_failed_attempt(record: PendingEmail, error: str) -> None:
        record.retry_count += 1
        record.last_error = error

        if record.retry_count >= 3:
            record.status = EmailSendingStatus.FAILED

    @staticmethod
    async def reset_for_retry(
        session: AsyncSession,
        record: PendingEmail,
    ) -> None:
        record.status = EmailSendingStatus.PENDING
        record.retry_count = 0
        record.last_error = None
