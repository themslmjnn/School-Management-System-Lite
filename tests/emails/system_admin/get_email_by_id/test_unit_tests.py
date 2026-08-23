from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.emails.service import PendingEmailService
from src.utils.exceptions import PendingEmailNotFoundError
from tests.factories import make_email


class TestGetEmailById:
    async def test_returns_correct_email(self, session: AsyncSession):
        email = await make_email(session)

        result = await PendingEmailService.get_email_by_id(session, email.id)

        assert result is not None
        assert result.id == email.id

    async def test_returns_none_when_not_found(self, session: AsyncSession):
        with pytest.raises(PendingEmailNotFoundError):
            await PendingEmailService.get_email_by_id(session, 999_999)

    async def test_returns_email_for_valid_id(self, session: AsyncSession):
        email = await make_email(session)

        result = await PendingEmailService.get_email_by_id(session, email.id)

        assert result.id == email.id
        assert result.recipient == email.recipient

    async def test_raises_404_for_missing_id(self, session: AsyncSession):
        with pytest.raises(PendingEmailNotFoundError):
            await PendingEmailService.get_email_by_id(session, 999_999)

    async def test_caches_result_on_first_call(
        self, session: AsyncSession, mock_set_cache_email
    ):
        email = await make_email(session)

        await PendingEmailService.get_email_by_id(session, email.id)

        mock_set_cache_email.assert_awaited_once()

    async def test_returns_from_cache_without_hitting_db(
        self, session: AsyncSession, mocker
    ):
        email = await make_email(session)

        await PendingEmailService.get_email_by_id(session, email.id)

        mock_repo = mocker.patch(
            "src.emails.service.PendingEmailRepository.get_email_by_id",
            new_callable=AsyncMock,
        )

        await PendingEmailService.get_email_by_id(session, email.id)

        mock_repo.assert_not_awaited()
