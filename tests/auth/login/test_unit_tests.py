from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import AuthService
from src.users.repositories.user import UserRepositoryBase
from src.utils.base_exception import (
    AccountInactiveError,
    AccountLockedError,
    EmptyCredentialsError,
    InvalidCredentialsError,
)
from src.utils.enums import UserStatus
from tests.conftest import user_form
from tests.factories import (
    make_deactivated_user,
    make_teacher,
)


class TestLogin:
    async def test_raises_on_empty_username(self, session: AsyncSession, mock_response):
        form = user_form(username=None, password="pass")

        with pytest.raises(EmptyCredentialsError):
            await AuthService.login(session, mock_response, form)

    async def test_raises_on_empty_password(self, session: AsyncSession, mock_response):
        form = user_form(username="user", password=None)

        with pytest.raises(EmptyCredentialsError):
            await AuthService.login(session, mock_response, form)

    async def test_raises_invalid_credentials_for_unknown_user(
        self, session: AsyncSession, mock_response
    ):
        form = user_form(username="nobody", password="pass")

        with pytest.raises(InvalidCredentialsError):
            await AuthService.login(session, mock_response, form)

    async def test_raises_invalid_credentials_for_wrong_password(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(session, username="wrongpass_user")
        form = user_form(username=user.username, password="WrongPassword!")

        with pytest.raises(InvalidCredentialsError):
            await AuthService.login(session, mock_response, form)

    async def test_raises_invalid_credentials_when_no_password_set(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(
            session,
            username="nopwd_user",
            password=None,
            status=UserStatus.PENDING_ACTIVATION,
            is_active=False,
        )
        form = user_form(username=user.username, password="AnyPassword1!")

        with pytest.raises(InvalidCredentialsError):
            await AuthService.login(session, mock_response, form)

    async def test_raises_invalid_credentials_for_pending_activation(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(
            session,
            username="pending_user",
            status=UserStatus.PENDING_ACTIVATION,
            is_active=False,
        )
        form = user_form(username=user.username, password="TestPassword123!")

        with pytest.raises(InvalidCredentialsError):
            await AuthService.login(session, mock_response, form)

    async def test_raises_account_inactive_for_deactivated_user(
        self, session: AsyncSession, mock_response
    ):
        user = await make_deactivated_user(session, username="deactivated_login")
        form = user_form(username=user.username, password="TestPassword123!")

        with pytest.raises(AccountInactiveError):
            await AuthService.login(session, mock_response, form)

    async def test_raises_account_locked_when_lockout_active(
        self, session: AsyncSession, mock_response
    ):
        locked_until = datetime.now(UTC) + timedelta(minutes=10)
        user = await make_teacher(
            session,
            username="locked_user",
            locked_until=locked_until,
        )
        form = user_form(username=user.username, password="TestPassword123!")

        with pytest.raises(AccountLockedError):
            await AuthService.login(session, mock_response, form)

    async def test_successful_login_returns_access_token(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(session, username="login_ok_user")
        form = user_form(username=user.username, password="TestPassword123!")
        response = mock_response

        result = await AuthService.login(session, response, form)

        assert result.access_token is not None
        assert result.token_type == "bearer"

    async def test_successful_login_sets_refresh_token_cookie(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(session, username="cookie_user")
        form = user_form(username=user.username, password="TestPassword123!")
        response = mock_response

        await AuthService.login(session, response, form)

        response.set_cookie.assert_called()
        cookie_calls = [
            call.kwargs["key"] for call in response.set_cookie.call_args_list
        ]

        assert "refresh_token" in cookie_calls
        assert "refresh_token_family" in cookie_calls

    async def test_successful_login_resets_failed_attempts(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(
            session,
            username="reset_attempts_user",
            failed_login_attempts=3,
        )
        form = user_form(username=user.username, password="TestPassword123!")

        await AuthService.login(session, mock_response, form)

        refreshed = await UserRepositoryBase.get_user_by_username(
            session, user.username, load_login_lockout=True
        )

        assert refreshed.login_lockout.failed_login_attempts == 0
        assert refreshed.login_lockout.locked_until is None

    async def test_failed_login_increments_attempt_counter(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(session, username="attempt_counter_user")
        form = user_form(username=user.username, password="WrongPassword!")

        with pytest.raises(InvalidCredentialsError):
            await AuthService.login(session, mock_response, form)

        refreshed = await UserRepositoryBase.get_user_by_username(
            session, user.username, load_login_lockout=True
        )

        assert refreshed.login_lockout.failed_login_attempts == 1

    async def test_five_failures_trigger_lockout(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(
            session,
            username="lockout_trigger_user",
            failed_login_attempts=4,
        )
        form = user_form(username=user.username, password="WrongPassword!")

        with pytest.raises(InvalidCredentialsError):
            await AuthService.login(session, mock_response, form)

        refreshed = await UserRepositoryBase.get_user_by_username(
            session, user.username, load_login_lockout=True
        )

        assert refreshed.login_lockout.locked_until is not None
        assert refreshed.login_lockout.locked_until > datetime.now(UTC)

    async def test_successful_login_persists_refresh_token_hash(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(session, username="token_persist_user")
        form = user_form(username=user.username, password="TestPassword123!")

        await AuthService.login(session, mock_response, form)

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )

        assert refreshed.session.refresh_token_hash is not None
        assert refreshed.session.refresh_token_family is not None
        assert refreshed.session.refresh_token_expires_at is not None
