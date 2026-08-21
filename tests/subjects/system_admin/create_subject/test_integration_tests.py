from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_subject


class TestCreateSubject:
    async def test_returns_201_with_correct_data(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            "/subjects",
            json={"name": "Mathematics", "code": "MATH201"},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 201
        assert body["name"] == "Mathematics"
        assert body["code"] == "MATH201"
        assert body["id"] is not None
        assert body["is_archived"] is False

    async def test_returns_409_for_duplicate_code(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_subject(session, name="Existing", code="DUP201")
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            "/subjects",
            json={"name": "Duplicate Subject", "code": "DUP201"},
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
            "/subjects",
            json={"name": "Hi", "code": "VALID101"},
            headers=headers,
        )

        assert response.status_code == 422

    async def test_returns_422_for_short_code(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            "/subjects",
            json={"name": "Valid Subject Name", "code": "AB"},
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
            "/subjects",
            json={"name": "Mathematics", "code": "MATH301"},
            headers=headers,
        )

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/subjects",
            json={"name": "Mathematics", "code": "MATH401"},
        )

        assert response.status_code == 401
