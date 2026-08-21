from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_group


class TestGetGroupByIdEndpoint:
    async def test_returns_200_with_correct_data(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        group = await make_group(session, name="RT DET GG", academic_year=2025)
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/groups/{group.id}", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == group.id
        assert body["name"] == group.name
        assert body["academic_year"] == group.academic_year
        assert "is_archived" in body

    async def test_archived_group_is_returned(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        group = await make_group(
            session,
            name="ARCH RT DET GG",
            academic_year=2025,
            is_archived=True,
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/groups/{group.id}", headers=headers)

        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    async def test_returns_404_when_not_found(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/groups/999999", headers=headers)

        assert response.status_code == 404

    async def test_forbidden_for_director(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        group = await make_group(session, name="DIR DET GG", academic_year=2025)
        headers = await make_auth_header(session, director)

        response = await client.get(f"/groups/{group.id}", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/groups/1")

        assert response.status_code == 401

    async def test_returns_422_for_invalid_path_id(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/groups/0", headers=headers)

        assert response.status_code == 422
