from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_teacher


class TestGetGuardiansEndpoint:
    async def test_returns_200_with_guardians_only(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        guardian: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get("/users/guardians", headers=headers)

        body = response.json()
        returned_roles = {item["role"] for item in body["items"]}

        assert response.status_code == 200
        assert guardian.role in returned_roles
        assert teacher.role not in returned_roles

    async def test_forbidden_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.get("/users/guardians", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client):
        response = await client.get("/users/guardians")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get(
            "/users/guardians", params={"limit": 101}, headers=headers
        )

        assert response.status_code == 422

    async def test_query_param_cannot_override_role_scoping(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        teacher = await make_teacher(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get(
            "/users/guardians",
            params={"allowed_roles": "SYSTEM_ADMIN"},
            headers=headers,
        )

        returned_roles = {item["role"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert teacher.role not in returned_roles
