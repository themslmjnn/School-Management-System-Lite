from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.repositories.user import UserRepositoryBase
from tests.factories import make_teacher


class TestForgotPassword:
    async def test_returns_200_with_message_for_existing_user(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_forgot_ok")

        response = await client.post(
            "/auth/forgot-password",
            json={"username": user.username},
        )

        body = response.json()

        assert response.status_code == 200
        assert "detail" in body

    async def test_returns_200_with_same_message_for_nonexistent_user(
        self, client: AsyncClient
    ):
        """Username enumeration protection — same response either way."""
        response = await client.post(
            "/auth/forgot-password",
            json={"username": "ghost_forgot_int"},
        )

        body = response.json()

        assert response.status_code == 200
        assert "detail" in body

    async def test_stores_reset_token_for_existing_user(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="forgot_stores_token")

        await client.post(
            "/auth/forgot-password",
            json={"username": user.username},
        )

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )

        assert refreshed.session.reset_password_token_hash is not None
        assert refreshed.session.reset_password_token_expires_at > datetime.now(UTC)

    async def test_username_too_short_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/auth/forgot-password",
            json={"username": "short"},
        )

        assert response.status_code == 422

    async def test_missing_body_returns_422(self, client: AsyncClient):
        response = await client.post("/auth/forgot-password", json={})

        assert response.status_code == 422
