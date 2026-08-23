from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import ResetPassword
from src.auth.service import AuthService
from src.core.security import generate_reset_password_token
from src.users.repositories.user import UserRepositoryBase
from utils.exceptions import (
    ExpiredResetPasswordTokenError,
    InvalidCredentialsError,
    InvalidResetPasswordTokenError,
)
from tests.factories import make_teacher


class TestResetPassword:
    async def test_resets_password_successfully(self, session: AsyncSession):

        user = await make_teacher(session, username="reset_pwd_user")

        raw_token, hashed_token = generate_reset_password_token()

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        u.session.reset_password_token_hash = hashed_token
        u.session.reset_password_token_expires_at = datetime.now(UTC) + timedelta(
            minutes=15
        )
        await session.commit()

        request = ResetPassword(
            username=user.username,
            reset_token=raw_token,
            new_password="BrandNew123!",
        )

        await AuthService.reset_password(session, request)

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )

        assert refreshed.session.reset_password_token_hash is None
        assert refreshed.session.reset_password_token_expires_at is None
        assert refreshed.session.refresh_token_hash is None
        assert refreshed.session.refresh_token_family is None

    async def test_raises_for_unknown_username(self, session: AsyncSession):

        request = ResetPassword(
            username="ghost_reset_user",
            reset_token="some_token",
            new_password="BrandNew123!",
        )

        with pytest.raises(InvalidCredentialsError):
            await AuthService.reset_password(session, request)

    async def test_raises_for_wrong_token(self, session: AsyncSession):

        user = await make_teacher(session, username="wrong_reset_token")

        _, hashed_token = generate_reset_password_token()

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        u.session.reset_password_token_hash = hashed_token
        u.session.reset_password_token_expires_at = datetime.now(UTC) + timedelta(
            minutes=15
        )
        await session.commit()

        request = ResetPassword(
            username=user.username,
            reset_token="completely_wrong",
            new_password="BrandNew123!",
        )

        with pytest.raises(InvalidResetPasswordTokenError):
            await AuthService.reset_password(session, request)

    async def test_raises_for_expired_token(self, session: AsyncSession):

        user = await make_teacher(session, username="expired_reset_user")

        raw_token, hashed_token = generate_reset_password_token()

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        u.session.reset_password_token_hash = hashed_token
        u.session.reset_password_token_expires_at = datetime.now(UTC) - timedelta(
            seconds=1
        )
        await session.commit()

        request = ResetPassword(
            username=user.username,
            reset_token=raw_token,
            new_password="BrandNew123!",
        )

        with pytest.raises(ExpiredResetPasswordTokenError):
            await AuthService.reset_password(session, request)

    async def test_reset_increments_access_token_version(self, session: AsyncSession):

        user = await make_teacher(session, username="reset_version_user")

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        version_before = u.session.access_token_version

        raw_token, hashed_token = generate_reset_password_token()
        u.session.reset_password_token_hash = hashed_token
        u.session.reset_password_token_expires_at = datetime.now(UTC) + timedelta(
            minutes=15
        )
        await session.commit()

        request = ResetPassword(
            username=user.username,
            reset_token=raw_token,
            new_password="BrandNew123!",
        )

        await AuthService.reset_password(session, request)

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )

        assert refreshed.session.access_token_version == version_before + 1

    async def test_reset_clears_login_lockout(self, session: AsyncSession):
        locked_until = datetime.now(UTC) + timedelta(minutes=5)
        user = await make_teacher(
            session,
            username="reset_lockout_user",
            failed_login_attempts=5,
            locked_until=locked_until,
        )

        raw_token, hashed_token = generate_reset_password_token()

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        u.session.reset_password_token_hash = hashed_token
        u.session.reset_password_token_expires_at = datetime.now(UTC) + timedelta(
            minutes=15
        )
        await session.commit()

        request = ResetPassword(
            username=user.username,
            reset_token=raw_token,
            new_password="BrandNew123!",
        )

        await AuthService.reset_password(session, request)

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_login_lockout=True
        )

        assert refreshed.login_lockout.failed_login_attempts == 0
        assert refreshed.login_lockout.locked_until is None
