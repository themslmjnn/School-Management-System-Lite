from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_subject


class TestDirectorGetSubjectByIdEndpoint:
    async def test_returns_200_with_correct_data(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        subject = await make_subject(
            session, name="Dir Route Detail", code="DIRRDET301"
        )
        headers = await make_auth_header(session, director)

        response = await client.get(f"/director/subjects/{subject.id}", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["name"] == subject.name
        assert body["code"] == subject.code

    async def test_response_excludes_archived_at(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        subject = await make_subject(
            session, name="Dir Schema Route Detail", code="DIRSCHRT301"
        )
        headers = await make_auth_header(session, director)

        response = await client.get(f"/director/subjects/{subject.id}", headers=headers)

        assert response.status_code == 200
        assert "archived_at" not in response.json()

    async def test_returns_404_when_not_found(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        headers = await make_auth_header(session, director)

        response = await client.get("/director/subjects/999999", headers=headers)

        assert response.status_code == 404

    async def test_forbidden_for_system_admin(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        subject = await make_subject(
            session, name="Dir Admin Forbidden", code="DIRADMFB301"
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/director/subjects/{subject.id}", headers=headers)

        assert response.status_code == 403

    async def test_forbidden_for_teacher(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        subject = await make_subject(
            session, name="Dir Teacher Forbidden", code="DIRTEAFB301"
        )
        headers = await make_auth_header(session, teacher)

        response = await client.get(f"/director/subjects/{subject.id}", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/director/subjects/1")

        assert response.status_code == 401

    async def test_returns_422_for_invalid_path_id(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        headers = await make_auth_header(session, director)

        response = await client.get("/director/subjects/0", headers=headers)

        assert response.status_code == 422
