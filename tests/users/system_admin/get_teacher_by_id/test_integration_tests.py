from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import UserRole
from tests.conftest import make_auth_header
from tests.factories import make_teacher


class TestGetTeacherById:
    async def test_returns_200_with_correct_data(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/users/teachers/{teacher.id}", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == teacher.id
        assert body["role"] == UserRole.TEACHER.value

    async def test_returns_404_when_not_found(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/users/teachers/999999", headers=headers)

        assert response.status_code == 404

    async def test_returns_404_for_non_staff_role(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        student: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/users/teachers/{student.id}", headers=headers)

        assert response.status_code == 404

    async def test_forbidden_for_non_admin(
        self, session: AsyncSession, client: AsyncClient, teacher: User
    ):
        other_teacher = await make_teacher(session)
        headers = await make_auth_header(session, teacher)

        response = await client.get(
            f"/users/teachers/{other_teacher.id}", headers=headers
        )

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, teacher: User
    ):
        response = await client.get(f"/users/teachers/{teacher.id}")

        assert response.status_code == 401

    async def test_invalid_path_id_returns_422(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/users/teachers/0", headers=headers)

        assert response.status_code == 422
