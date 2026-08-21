from datetime import UTC, datetime
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import AuthService
from src.users.repositories.user import UserRepositoryBase
from tests.factories import make_teacher


class TestForgotPassword:
    async def test_returns_message_for_existing_user(self, session: AsyncSession):
        from src.auth.schemas import ForgotPasswordPublicRequest

        user = await make_teacher(session, username="forgot_ok_user")
        request = ForgotPasswordPublicRequest(username=user.username)

        result = await AuthService.create_forgot_password_request(session, request)

        assert result.detail is not None

    async def test_returns_same_message_for_nonexistent_user(
        self, session: AsyncSession
    ):
        """Must not leak whether a username exists."""
        from src.auth.schemas import ForgotPasswordPublicRequest

        request = ForgotPasswordPublicRequest(username="ghost_forgot_user")

        result = await AuthService.create_forgot_password_request(session, request)

        assert result.detail is not None

    async def test_stores_reset_token_for_existing_user(self, session: AsyncSession):
        from src.auth.schemas import ForgotPasswordPublicRequest

        user = await make_teacher(session, username="forgot_token_user")
        request = ForgotPasswordPublicRequest(username=user.username)

        await AuthService.create_forgot_password_request(session, request)

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )

        assert refreshed.session.reset_password_token_hash is not None
        assert refreshed.session.reset_password_token_expires_at is not None
        assert refreshed.session.reset_password_token_expires_at > datetime.now(UTC)

    async def test_does_not_store_token_for_nonexistent_user(
        self, session: AsyncSession, mocker
    ):
        """Non-existent users: no DB writes, no errors."""
        from src.auth.schemas import ForgotPasswordPublicRequest

        mock_commit = mocker.patch.object(session, "commit", new_callable=AsyncMock)
        request = ForgotPasswordPublicRequest(username="ghost_no_write_user")

        await AuthService.create_forgot_password_request(session, request)

        mock_commit.assert_not_called()
