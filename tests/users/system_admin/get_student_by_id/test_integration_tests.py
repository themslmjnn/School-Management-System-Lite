from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_group, make_student


class TestGetStudentById:
    async def test_returns_200_with_correct_data(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        student: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/users/students/{student.id}", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == student.id
        assert body["email"] == student.email
        assert "group" in body

    async def test_group_null_when_student_has_no_group(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        student: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/users/students/{student.id}", headers=headers)

        assert response.status_code == 200
        assert response.json()["group"] is None

    async def test_group_populated_when_student_has_group(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        group = await make_group(session)
        student = await make_student(
            session, username="grouped_student", group_id=group.id
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/users/students/{student.id}", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["group"] is not None
        assert body["group"]["name"] == group.name

    async def test_returns_404_when_not_found(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/users/students/999999", headers=headers)

        assert response.status_code == 404

    async def test_returns_404_for_non_student(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/users/students/{teacher.id}", headers=headers)

        assert response.status_code == 404

    async def test_forbidden_for_non_admin(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
        student: User,
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.get(f"/users/students/{student.id}", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, student: User
    ):
        response = await client.get(f"/users/students/{student.id}")

        assert response.status_code == 401

    async def test_invalid_path_id_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/users/students/0", headers=headers)

        assert response.status_code == 422
