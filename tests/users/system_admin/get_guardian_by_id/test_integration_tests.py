from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import UserRole
from tests.conftest import make_auth_header


class TestGetGuardianByIdEndpoint:
    async def test_returns_200_with_correct_data(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        guardian: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get(f"/users/guardians/{guardian.id}", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == guardian.id
        assert body["role"] == UserRole.GUARDIAN.value

    async def test_returns_404_when_not_found(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get("/users/guardians/999999", headers=headers)

        assert response.status_code == 404

    async def test_returns_404_for_non_guardian_role(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get(f"/users/guardians/{teacher.id}", headers=headers)

        assert response.status_code == 404

    async def test_forbidden_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User, guardian: User
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.get(f"/users/guardians/{guardian.id}", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, guardian: User
    ):
        response = await client.get(f"/users/guardians/{guardian.id}")

        assert response.status_code == 401

    async def test_invalid_path_id_returns_422(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get("/users/guardians/0", headers=headers)

        assert response.status_code == 422
