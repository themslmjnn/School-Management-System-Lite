from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_group


class TestCreateGroupEndpoint:
    async def test_returns_201_with_correct_data(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            "/groups",
            json={"name": "RT GRP A", "academic_year": 2025},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 201
        assert body["name"] == "RT GRP A"
        assert body["academic_year"] == 2025
        assert body["id"] is not None
        assert body["is_archived"] is False

    async def test_returns_409_for_duplicate_name_and_year(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_group(session, name="DUP RT", academic_year=2025)
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            "/groups",
            json={"name": "DUP RT", "academic_year": 2025},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_returns_422_for_short_name(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            "/groups",
            json={"name": "A", "academic_year": 2025},
            headers=headers,
        )

        assert response.status_code == 422

    async def test_returns_422_for_invalid_academic_year(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            "/groups",
            json={"name": "GRP YR", "academic_year": 1999},
            headers=headers,
        )

        assert response.status_code == 422

    async def test_returns_422_for_zero_capacity(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            "/groups",
            json={"name": "GRP CAP", "academic_year": 2025, "capacity": 0},
            headers=headers,
        )

        assert response.status_code == 422

    async def test_forbidden_for_director(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        headers = await make_auth_header(session, director)

        response = await client.post(
            "/groups",
            json={"name": "DIR GRP", "academic_year": 2025},
            headers=headers,
        )

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/groups",
            json={"name": "UNAUTH GRP", "academic_year": 2025},
        )

        assert response.status_code == 401
