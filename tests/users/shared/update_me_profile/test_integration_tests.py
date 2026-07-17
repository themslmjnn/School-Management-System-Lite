from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header


class TestUpdateMeProfile:
    async def test_guardian_returns_200_with_updated_field(
        self, test_db: AsyncSession, client: AsyncClient, guardian: User
    ):
        headers = await make_auth_header(test_db, guardian)

        response = await client.patch(
            "/users/me/profile",
            json={"firstname": "HttpUpdated"},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["firstname"] == "Httpupdated"

    async def test_forbidden_for_role_outside_editable_set(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.patch(
            "/users/me/profile",
            json={"firstname": "ShouldBeBlocked"},
            headers=headers,
        )

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.patch("/users/me/profile", json={"firstname": "NoAuth"})

        assert response.status_code == 401

    async def test_invalid_firstname_returns_422(
        self, test_db: AsyncSession, client: AsyncClient, guardian: User
    ):
        headers = await make_auth_header(test_db, guardian)

        response = await client.patch(
            "/users/me/profile",
            json={"firstname": "123invalid"},
            headers=headers,
        )

        assert response.status_code == 422
