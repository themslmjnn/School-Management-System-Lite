from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import ActivateAccountWithToken
from src.auth.service import AuthService
from src.core.security import generate_invite_token
from src.users.repositories.user import UserRepositoryBase
from src.utils.enums import UserStatus
from src.utils.exceptions import ExpiredInviteTokenError, InvalidInviteTokenError
from tests.factories import make_teacher


class TestActivateAccountWithToken:
    async def test_activates_user_and_sets_password(self, session: AsyncSession):
        from src.auth.schemas import ActivateAccountWithToken

        user = await make_teacher(
            session,
            username="activate_ok_user",
            status=UserStatus.PENDING_ACTIVATION,
            is_active=False,
            password=None,
        )

        raw_token, hashed_token = generate_invite_token()

        u = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_activation=True
        )
        u.activation.invite_token_hash = hashed_token
        u.activation.invite_token_expires_at = datetime.now(UTC) + timedelta(hours=24)
        await session.commit()

        request = ActivateAccountWithToken(
            username=user.username,
            invite_token=raw_token,
            new_password="NewPassword123!",
        )

        await AuthService.activate_account(session, request)

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_activation=True
        )

        assert refreshed.is_active is True
        assert refreshed.status == UserStatus.ACTIVE
        assert refreshed.password_hash is not None
        assert refreshed.activation.invite_token_hash is None
        assert refreshed.activation.invite_token_expires_at is None

    async def test_raises_for_unknown_username(self, session: AsyncSession):
        request = ActivateAccountWithToken(
            username="ghost_user",
            invite_token="some_token",
            new_password="NewPassword123!",
        )

        with pytest.raises(InvalidInviteTokenError):
            await AuthService.activate_account(session, request)

    async def test_raises_for_wrong_token(self, session: AsyncSession):
        user = await make_teacher(
            session,
            username="wrong_token_user",
            status=UserStatus.PENDING_ACTIVATION,
            is_active=False,
            password=None,
        )

        _, hashed_token = generate_invite_token()

        u = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_activation=True
        )
        u.activation.invite_token_hash = hashed_token
        u.activation.invite_token_expires_at = datetime.now(UTC) + timedelta(hours=24)
        await session.commit()

        request = ActivateAccountWithToken(
            username=user.username,
            invite_token="definitely_wrong_token",
            new_password="NewPassword123!",
        )

        with pytest.raises(InvalidInviteTokenError):
            await AuthService.activate_account(session, request)

    async def test_raises_for_expired_token(self, session: AsyncSession):
        user = await make_teacher(
            session,
            username="expired_token_user",
            status=UserStatus.PENDING_ACTIVATION,
            is_active=False,
            password=None,
        )

        raw_token, hashed_token = generate_invite_token()

        u = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_activation=True
        )
        u.activation.invite_token_hash = hashed_token
        u.activation.invite_token_expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()

        request = ActivateAccountWithToken(
            username=user.username,
            invite_token=raw_token,
            new_password="NewPassword123!",
        )

        with pytest.raises(ExpiredInviteTokenError):
            await AuthService.activate_account(session, request)
