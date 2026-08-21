from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_subject


class TestUpdateSubjectEndpoint:
    async def test_returns_204_on_success(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        subject = await make_subject(session, name="Patchable Subject", code="PATCH101")
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/subjects/{subject.id}",
            json={"name": "Patched Subject Name"},
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
            "/subjects/999999",
            json={"name": "Doesnt Matter Name"},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_returns_409_for_no_changes(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        subject = await make_subject(session, name="No Change Subject", code="NOCH201")
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/subjects/{subject.id}",
            json={},
            headers=headers,
        )

        assert response.status_code == 400

    async def test_returns_409_for_duplicate_code(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_subject(session, name="Taken Subject", code="TAKEN201")
        target = await make_subject(session, name="Target Subject", code="TARGET201")
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/subjects/{target.id}",
            json={"code": "TAKEN201"},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_forbidden_for_director(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        subject = await make_subject(session, name="Dir Subject", code="DIR101")
        headers = await make_auth_header(session, director)

        response = await client.patch(
            f"/subjects/{subject.id}",
            json={"name": "Director Patch Attempt"},
            headers=headers,
        )

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.patch(
            "/subjects/1",
            json={"name": "Doesnt Matter Name"},
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
            "/subjects/0",
            json={"name": "Doesnt Matter Name"},
            headers=headers,
        )

        assert response.status_code == 422
