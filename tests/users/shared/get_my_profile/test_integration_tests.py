from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header


class TestGetMyProfile:
    async def test_returns_200_for_teacher(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)
        response = await client.get("/users/me", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == teacher.id
        assert body["username"] == teacher.username

    async def test_returns_200_for_director(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        headers = await make_auth_header(session, director)
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 200
        assert response.json()["id"] == director.id

    async def test_response_excludes_phone_number_field(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)
        response = await client.get("/users/me", headers=headers)

        body = response.json()

        assert "phone_number" not in body
        assert "format_phone_number" in body

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/users/me")

        assert response.status_code == 401

    async def test_student_gets_404_on_me(
        self,
        session: AsyncSession,
        client: AsyncClient,
        student: User,
    ):
        headers = await make_auth_header(session, student)
        response = await client.get("/users/me", headers=headers)

        assert response.status_code == 404
