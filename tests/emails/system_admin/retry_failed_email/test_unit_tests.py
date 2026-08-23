import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.emails.repository import PendingEmailRepository
from src.emails.service import PendingEmailService
from utils.exceptions import PendingEmailNotFoundError
from src.utils.enums import EmailSendingStatus
from tests.factories import make_email


class TestRetryFailedEmail:
    async def test_resets_failed_email_to_pending(self, session: AsyncSession):
        email = await make_email(
            session,
            status=EmailSendingStatus.FAILED,
            retry_count=3,
            last_error="Connection refused",
        )

        await PendingEmailService.retry_failed_email(session, email.id)

        refreshed = await PendingEmailRepository.get_email_by_id(session, email.id)

        assert refreshed.status == EmailSendingStatus.PENDING
        assert refreshed.retry_count == 0
        assert refreshed.last_error is None

    async def test_raises_404_for_missing_id(self, session: AsyncSession):
        with pytest.raises(PendingEmailNotFoundError):
            await PendingEmailService.retry_failed_email(session, 999_999)

    async def test_works_on_pending_email_too(self, session: AsyncSession):
        email = await make_email(
            session,
            status=EmailSendingStatus.PENDING,
            retry_count=2,
            last_error="Timeout",
        )

        await PendingEmailService.retry_failed_email(session, email.id)

        refreshed = await PendingEmailRepository.get_email_by_id(session, email.id)

        assert refreshed.status == EmailSendingStatus.PENDING
        assert refreshed.retry_count == 0
        assert refreshed.last_error is None

    async def test_commits_changes_to_db(self, session: AsyncSession):
        email = await make_email(
            session,
            status=EmailSendingStatus.FAILED,
            retry_count=3,
        )

        await PendingEmailService.retry_failed_email(session, email.id)

        result = await PendingEmailRepository.get_email_by_id(session, email.id)

        assert result.status == EmailSendingStatus.PENDING
