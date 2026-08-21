from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_group


class TestArchiveGroupEndpoint:
    async def test_returns_204_on_success(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        group = await make_group(session, name="TO ARCH RT", academic_year=2025)
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(f"/groups/{group.id}/archive", headers=headers)

        assert response.status_code == 204

    async def test_returns_404_when_not_found(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch("/groups/999999/archive", headers=headers)

        assert response.status_code == 404

    async def test_returns_409_when_already_archived(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        group = await make_group(
            session,
            name="AL ARCH RT",
            academic_year=2025,
            is_archived=True,
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(f"/groups/{group.id}/archive", headers=headers)

        assert response.status_code == 409

    async def test_forbidden_for_director(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        group = await make_group(session, name="DIR ARCH RT", academic_year=2025)
        headers = await make_auth_header(session, director)

        response = await client.patch(f"/groups/{group.id}/archive", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.patch("/groups/1/archive")

        assert response.status_code == 401

    async def test_returns_422_for_invalid_path_id(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch("/groups/0/archive", headers=headers)

        assert response.status_code == 422
