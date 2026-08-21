from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generate_email_change_code
from src.users.repositories.user import UserRepositoryBase
from src.users.schemas.shared import ConfirmEmailChange
from src.users.services.shared import UserServiceSelf
from src.users.utils.exceptions import (
    EmailChangeCodeExpiredError,
    InvalidEmailChangeCodeError,
    NoPendingEmailChangeError,
)
from tests.factories import make_student, make_teacher


class TestConfirmEmailChange:
    async def _setup_pending_change(
        self,
        session: AsyncSession,
        user,
        new_email: str,
        minutes_until_expiry: int = 15,
    ) -> str:
        raw_code, hashed_code = generate_email_change_code()

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        u.session.pending_new_email = new_email
        u.session.email_change_code_hash = hashed_code
        u.session.email_change_code_expires_at = datetime.now(UTC) + timedelta(
            minutes=minutes_until_expiry
        )
        await session.commit()

        return raw_code

    async def test_confirms_email_for_non_student(
        self, session: AsyncSession, mock_send_email_changed_notification
    ):
        user = await make_teacher(session, username="confirm_email")
        new_email = "confirmed_teacher@example.com"
        raw_code = await self._setup_pending_change(session, user, new_email)

        await UserServiceSelf.confirm_email_change(
            session, user.id, ConfirmEmailChange(code=raw_code)
        )

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
        assert refreshed.email == new_email
        assert refreshed.session.pending_new_email is None
        assert refreshed.session.email_change_code_hash is None

    async def test_confirm_invalidates_all_tokens(
        self, session: AsyncSession, mock_send_email_changed_notification
    ):
        user = await make_teacher(session, username="confirm_email")
        raw_code = await self._setup_pending_change(
            session, user, "tokens_invalidated@example.com"
        )

        u_before = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
        version_before = u_before.session.access_token_version

        await UserServiceSelf.confirm_email_change(
            session, user.id, ConfirmEmailChange(code=raw_code)
        )

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
        assert refreshed.session.access_token_version == version_before + 1
        assert refreshed.session.refresh_token_hash is None
        assert refreshed.session.refresh_token_family is None

    async def test_raises_when_no_pending_change(self, session: AsyncSession):
        user = await make_teacher(session, username="confirm_no_pending")

        with pytest.raises(NoPendingEmailChangeError):
            await UserServiceSelf.confirm_email_change(
                session, user.id, ConfirmEmailChange(code="123456")
            )

    async def test_raises_on_expired_code(self, session: AsyncSession):
        user = await make_teacher(session, username="confirm_expired")
        raw_code = await self._setup_pending_change(
            session, user, "expired@example.com", minutes_until_expiry=-1
        )

        with pytest.raises(EmailChangeCodeExpiredError):
            await UserServiceSelf.confirm_email_change(
                session, user.id, ConfirmEmailChange(code=raw_code)
            )

    async def test_raises_on_wrong_code(self, session: AsyncSession):
        user = await make_teacher(session, username="confirm_wrong")
        await self._setup_pending_change(session, user, "wrong_code@example.com")

        with pytest.raises(InvalidEmailChangeCodeError):
            await UserServiceSelf.confirm_email_change(
                session, user.id, ConfirmEmailChange(code="000000")
            )

    async def test_student_email_change_succeeds(
        self,
        session: AsyncSession,
        mock_send_email_changed_notification,
        mock_check_contact_limit_shared,
        mock_advisory_lock_shared,
    ):
        user = await make_student(session, username="confirm_email")
        new_email = "student_new@example.com"
        raw_code = await self._setup_pending_change(session, user, new_email)

        await UserServiceSelf.confirm_email_change(
            session, user.id, ConfirmEmailChange(code=raw_code)
        )

        refreshed = await UserRepositoryBase.get_user_by_id(session, user.id)
        assert refreshed.email == new_email
