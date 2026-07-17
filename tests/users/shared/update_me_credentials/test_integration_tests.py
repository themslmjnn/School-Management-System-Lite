from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_teacher


class TestUpdateMeCredentials:
    async def test_returns_204(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            "/users/me/credentials",
            json={"username": "http_self_username"},
            headers=headers,
        )

        assert response.status_code == 204

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.patch(
            "/users/me/credentials", json={"username": "doesntmatter123"}
        )

        assert response.status_code == 401

    async def test_returns_409_for_duplicate_username(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User
    ):
        await make_teacher(test_db, username="http_taken_username")
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            "/users/me/credentials",
            json={"username": "http_taken_username"},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_short_username_returns_422(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            "/users/me/credentials",
            json={"username": "abc"},
            headers=headers,
        )

        assert response.status_code == 422
