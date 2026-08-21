from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_group, make_student


class TestGetMyStudentProfile:
    async def test_returns_200_for_student(
        self,
        session: AsyncSession,
        client: AsyncClient,
        student,
    ):
        headers = await make_auth_header(session, student)
        response = await client.get("/users/students/me", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == student.id
        assert body["username"] == student.username

    async def test_returns_group_when_assigned(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        group = await make_group(session, name="Student Group Test")
        user = await make_student(
            session, username="student_with_group", group_id=group.id
        )
        headers = await make_auth_header(session, user)

        response = await client.get("/users/students/me", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["group"] is not None

    async def test_returns_null_group_when_not_assigned(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_student(session, username="student_no_group_int")
        headers = await make_auth_header(session, user)

        response = await client.get("/users/students/me", headers=headers)

        assert response.status_code == 200
        assert response.json()["group"] is None

    async def test_teacher_gets_403_on_students_me(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)
        response = await client.get("/users/students/me", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/users/students/me")

        assert response.status_code == 401
