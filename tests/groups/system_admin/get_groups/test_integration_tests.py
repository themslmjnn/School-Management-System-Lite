from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_group


class TestGetGroupsEndpoint:
    async def test_returns_200_with_active_groups_only(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        active = await make_group(session, name="ACTIVE RT", academic_year=2025)
        await make_group(
            session,
            name="ARCHIVED RT",
            academic_year=2025,
            is_archived=True,
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/groups", headers=headers)

        body = response.json()
        returned_names = {item["name"] for item in body["items"]}

        assert response.status_code == 200
        assert active.name in returned_names
        assert "ARCHIVED RT" not in returned_names

    async def test_include_archived_via_query_param(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_group(session, name="ACTIVE QP", academic_year=2025)
        archived = await make_group(
            session,
            name="ARCHIVED QP",
            academic_year=2025,
            is_archived=True,
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.get(
            "/groups",
            params={"include_archived": True},
            headers=headers,
        )

        returned_names = {item["name"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert archived.name in returned_names

    async def test_filter_by_name_via_query_param(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_group(session, name="FINDABLE", academic_year=2025)
        await make_group(session, name="OTHER GG", academic_year=2025)
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/groups", params={"name": "FIND"}, headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == "FINDABLE"

    async def test_filter_by_academic_year_via_query_param(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        target = await make_group(session, name="YEAR QP", academic_year=2022)
        await make_group(session, name="OTHER YR QP", academic_year=2023)
        headers = await make_auth_header(session, system_admin)

        response = await client.get(
            "/groups", params={"academic_year": 2022}, headers=headers
        )

        body = response.json()

        assert response.status_code == 200
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == target.name

    async def test_pagination_returns_correct_page(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        for i in range(3):
            await make_group(session, name=f"PG GG{i}", academic_year=2040 + i)

        headers = await make_auth_header(session, system_admin)

        response = await client.get(
            "/groups", params={"skip": 0, "limit": 2}, headers=headers
        )

        body = response.json()

        assert response.status_code == 200
        assert len(body["items"]) == 2
        assert body["total"] == 3
        assert body["has_more"] is True

    async def test_forbidden_for_director(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        headers = await make_auth_header(session, director)

        response = await client.get("/groups", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/groups")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/groups", params={"limit": 101}, headers=headers)

        assert response.status_code == 422
