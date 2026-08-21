from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import generate_invite_token
from tests.factories import make_teacher
from users.repositories.user import UserRepositoryBase
from utils.enums import UserStatus


class TestActivateAccount:
    async def _make_pending_user_with_token(self, session: AsyncSession, username: str):
        user = await make_teacher(
            session,
            username=username,
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

        return user, raw_token

    async def test_returns_204_on_valid_token(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user, raw_token = await self._make_pending_user_with_token(
            session, "int_activate_ok"
        )

        response = await client.post(
            "/auth/activation",
            json={
                "username": user.username,
                "invite_token": raw_token,
                "new_password": "ValidPass123!",
            },
        )

        assert response.status_code == 204

    async def test_user_is_active_after_activation(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user, raw_token = await self._make_pending_user_with_token(
            session, "int_activate_check"
        )

        await client.post(
            "/auth/activation",
            json={
                "username": user.username,
                "invite_token": raw_token,
                "new_password": "ValidPass123!",
            },
        )

        refreshed = await UserRepositoryBase.get_user_by_id(session, user.id)

        assert refreshed.is_active is True
        assert refreshed.status == UserStatus.ACTIVE

    async def test_returns_400_for_wrong_token(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user, _ = await self._make_pending_user_with_token(
            session, "activate_wrong_token"
        )

        response = await client.post(
            "/auth/activation",
            json={
                "username": user.username,
                "invite_token": "totally_wrong",
                "new_password": "ValidPass123!",
            },
        )

        assert response.status_code == 400

    async def test_returns_400_for_expired_token(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(
            session,
            username="int_activate_expired",
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

        response = await client.post(
            "/auth/activation",
            json={
                "username": user.username,
                "invite_token": raw_token,
                "new_password": "ValidPass123!",
            },
        )

        assert response.status_code == 400

    async def test_returns_400_for_unknown_user(self, client: AsyncClient):
        response = await client.post(
            "/auth/activation",
            json={
                "username": "nobody",
                "invite_token": "some_token",
                "new_password": "ValidPass123!",
            },
        )

        assert response.status_code == 400

    async def test_weak_password_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user, raw_token = await self._make_pending_user_with_token(
            session, "activate_weak_pwd"
        )

        response = await client.post(
            "/auth/activation",
            json={
                "username": user.username,
                "invite_token": raw_token,
                "new_password": "weak",
            },
        )

        assert response.status_code == 422
