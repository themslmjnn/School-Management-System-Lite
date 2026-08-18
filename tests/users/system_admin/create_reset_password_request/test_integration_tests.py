from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_system_admin


class TestCreateResetPasswordRequest:
    async def test_returns_204(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post(f"/users/{teacher.id}/password", headers=headers)

        assert response.status_code == 204

    async def test_returns_404_when_not_found(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post("/users/999999/password", headers=headers)

        assert response.status_code == 404

    async def test_returns_404_for_system_admin_target(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        other_admin = await make_system_admin(session)
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            f"/users/{other_admin.id}/password", headers=headers
        )

        assert response.status_code == 404

    async def test_returns_403_for_non_admin(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
        student: User,
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.post(f"/users/{student.id}/password", headers=headers)

        assert response.status_code == 403

    async def test_returns_401_when_unauthenticated(
        self,
        client: AsyncClient,
        teacher: User,
    ):
        response = await client.post(f"/users/{teacher.id}/password")

        assert response.status_code == 401

    async def test_returns_422_for_invalid_path_id(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post("/users/0/password", headers=headers)

        assert response.status_code == 422
