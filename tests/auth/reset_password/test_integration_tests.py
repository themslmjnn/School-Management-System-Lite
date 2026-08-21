from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generate_reset_password_token
from src.users.repositories.user import UserRepositoryBase
from tests.conftest import make_auth_header
from tests.factories import make_teacher


class TestResetPassword:
    async def _setup_reset_token(
        self, session: AsyncSession, user, minutes_from_now: int = 15
    ) -> str:
        raw_token, hashed_token = generate_reset_password_token()

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        u.session.reset_password_token_hash = hashed_token
        u.session.reset_password_token_expires_at = datetime.now(UTC) + timedelta(
            minutes=minutes_from_now
        )
        await session.commit()

        return raw_token

    async def test_returns_204_on_success(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_reset_ok")
        raw_token = await self._setup_reset_token(session, user)

        response = await client.post(
            "/auth/reset-password",
            json={
                "username": user.username,
                "reset_token": raw_token,
                "new_password": "BrandNew123!",
            },
        )

        assert response.status_code == 204

    async def test_old_token_invalid_after_reset(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher,
    ):
        headers_before = await make_auth_header(session, teacher)
        raw_token = await self._setup_reset_token(session, teacher)

        await client.post(
            "/auth/reset-password",
            json={
                "username": teacher.username,
                "reset_token": raw_token,
                "new_password": "BrandNew123!",
            },
        )

        # The old access token should now be rejected
        response = await client.post("/auth/logout", headers=headers_before)

        assert response.status_code == 401

    async def test_returns_401_for_unknown_username(self, client: AsyncClient):
        response = await client.post(
            "/auth/reset-password",
            json={
                "username": "ghost_reset",
                "reset_token": "some_token",
                "new_password": "BrandNew123!",
            },
        )

        assert response.status_code == 401

    async def test_returns_400_for_wrong_token(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="reset_wrong_token")
        await self._setup_reset_token(session, user)

        response = await client.post(
            "/auth/reset-password",
            json={
                "username": user.username,
                "reset_token": "wrong_token",
                "new_password": "BrandNew123!",
            },
        )

        assert response.status_code == 400

    async def test_returns_400_for_expired_token(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_reset_expired")
        raw_token = await self._setup_reset_token(session, user, minutes_from_now=-1)

        response = await client.post(
            "/auth/reset-password",
            json={
                "username": user.username,
                "reset_token": raw_token,
                "new_password": "BrandNew123!",
            },
        )

        assert response.status_code == 400

    async def test_weak_password_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_reset_weak_pwd")
        raw_token = await self._setup_reset_token(session, user)

        response = await client.post(
            "/auth/reset-password",
            json={
                "username": user.username,
                "reset_token": raw_token,
                "new_password": "weak",
            },
        )

        assert response.status_code == 422
