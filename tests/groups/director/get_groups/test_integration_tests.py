from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_group


class TestDirectorGetGroupsEndpoint:
    async def test_returns_200_with_active_groups_only(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        active = await make_group(session, name="DIR RT ACT", academic_year=2025)
        await make_group(
            session,
            name="DIR RT ARCH",
            academic_year=2025,
            is_archived=True,
        )
        headers = await make_auth_header(session, director)

        response = await client.get("/director/groups", headers=headers)

        body = response.json()
        returned_names = {item["name"] for item in body["items"]}

        assert response.status_code == 200
        assert active.name in returned_names
        assert "DIR RT ARCH" not in returned_names

    async def test_include_archived_param_ignored(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        await make_group(session, name="DIR QP ACT", academic_year=2025)
        archived = await make_group(
            session,
            name="DIR QP ARCH",
            academic_year=2025,
            is_archived=True,
        )
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/groups",
            params={"include_archived": True},
            headers=headers,
        )

        returned_names = {item["name"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert archived.name not in returned_names

    async def test_filter_by_name_via_query_param(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        await make_group(session, name="DIR FNDRT", academic_year=2025)
        await make_group(session, name="DIR OTHRT", academic_year=2025)
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/groups", params={"name": "FNDRT"}, headers=headers
        )

        body = response.json()

        assert response.status_code == 200
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == "DIR FNDRT"

    async def test_filter_by_academic_year_via_query_param(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        target = await make_group(session, name="DIR YR QP", academic_year=2019)
        await make_group(session, name="DIR OTH QP", academic_year=2020)
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/groups",
            params={"academic_year": 2019},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == target.name

    async def test_response_excludes_archived_at(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        await make_group(session, name="DIR SCHK", academic_year=2025)
        headers = await make_auth_header(session, director)

        response = await client.get("/director/groups", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert "archived_at" not in body["items"][0]

    async def test_forbidden_for_system_admin(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/director/groups", headers=headers)

        assert response.status_code == 403

    async def test_forbidden_for_teacher(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.get("/director/groups", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/director/groups")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/groups", params={"limit": 101}, headers=headers
        )

        assert response.status_code == 422
