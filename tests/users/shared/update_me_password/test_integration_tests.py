from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_teacher


class TestUpdateMePassword:
    async def test_returns_204_on_success(
        self,
        session: AsyncSession,
        client: AsyncClient,
        mock_send_password_changed_notification,
    ):
        user = await make_teacher(session, username="pwd_update_user")
        headers = await make_auth_header(session, user)

        response = await client.patch(
            "/users/me/password",
            json={
                "current_password": "TestPassword123!",
                "new_password": "BrandNew456!",
            },
            headers=headers,
        )

        assert response.status_code == 204

    async def test_old_token_rejected_after_password_change(
        self,
        session: AsyncSession,
        client: AsyncClient,
        mock_send_password_changed_notification,
    ):
        user = await make_teacher(session, username="pwd_token_user")
        headers = await make_auth_header(session, user)

        await client.patch(
            "/users/me/password",
            json={
                "current_password": "TestPassword123!",
                "new_password": "BrandNew456!",
            },
            headers=headers,
        )

        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 401

    async def test_returns_400_on_wrong_current_password(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.patch(
            "/users/me/password",
            json={
                "current_password": "WrongPassword!",
                "new_password": "BrandNew456!",
            },
            headers=headers,
        )

        assert response.status_code == 400

    async def test_returns_422_on_weak_new_password(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.patch(
            "/users/me/password",
            json={
                "current_password": "TestPassword123!",
                "new_password": "weak",
            },
            headers=headers,
        )

        assert response.status_code == 422

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.patch(
            "/users/me/password",
            json={
                "current_password": "TestPassword123!",
                "new_password": "BrandNew456!",
            },
        )

        assert response.status_code == 401

    async def test_missing_body_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)
        response = await client.patch("/users/me/password", json={}, headers=headers)

        assert response.status_code == 422
