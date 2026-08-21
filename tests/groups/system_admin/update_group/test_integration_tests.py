from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_group


class TestUpdateGroupEndpoint:
    async def test_returns_204_on_success(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        group = await make_group(
            session, name="PATCH", academic_year=2025
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/groups/{group.id}",
            json={"name": "PATCHED"},
            headers=headers,
        )

        assert response.status_code == 204

    async def test_returns_404_when_not_found(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            "/groups/999999",
            json={"name": "name"},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_returns_409_when_no_changes(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        group = await make_group(
            session, name="name", academic_year=2025
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/groups/{group.id}",
            json={"name": group.name},
            headers=headers,
        )

        assert response.status_code == 400

    async def test_returns_409_for_duplicate_name(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_group(session, name="TAKEN RT", academic_year=2025)
        target = await make_group(
            session, name="TARGET RT", academic_year=2025
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/groups/{target.id}",
            json={"name": "TAKEN RT"},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_returns_422_for_short_name(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        group = await make_group(
            session, name="VALID GRP", academic_year=2025
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/groups/{group.id}",
            json={"name": "A"},
            headers=headers,
        )

        assert response.status_code == 422

    async def test_returns_422_for_zero_capacity(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        group = await make_group(
            session, name="CAP RT GRP", academic_year=2025
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/groups/{group.id}",
            json={"name": "CAP RT GRP", "capacity": 0},
            headers=headers,
        )

        assert response.status_code == 422

    async def test_forbidden_for_director(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        group = await make_group(
            session, name="DIR RT GRP", academic_year=2025
        )
        headers = await make_auth_header(session, director)

        response = await client.patch(
            f"/groups/{group.id}",
            json={"name": "DIR RT UPD"},
            headers=headers,
        )

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.patch(
            "/groups/1",
            json={"name": "UNAUTH GRP"},
        )

        assert response.status_code == 401

    async def test_returns_422_for_invalid_path_id(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            "/groups/0",
            json={"name": "INVALID PATH"},
            headers=headers,
        )

        assert response.status_code == 422