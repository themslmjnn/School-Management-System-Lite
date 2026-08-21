from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_subject


class TestGetSubjectsEndpoint:
    async def test_returns_200_with_active_subjects(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        subject = await make_subject(session, name="Route Subject", code="ROUTE201")
        await make_subject(
            session,
            name="Archived Route Subject",
            code="RARCH201",
            is_archived=True,
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/subjects", headers=headers)

        body = response.json()
        returned_names = {item["name"] for item in body["items"]}

        assert response.status_code == 200
        assert subject.name in returned_names
        assert "Archived Route Subject" not in returned_names

    async def test_include_archived_via_query_param(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_subject(session, name="Active QP Subject", code="AQP201")
        archived = await make_subject(
            session,
            name="Archived QP Subject",
            code="ARCHQP201",
            is_archived=True,
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.get(
            "/subjects",
            params={"include_archived": True},
            headers=headers,
        )

        body = response.json()
        returned_names = {item["name"] for item in body["items"]}

        assert response.status_code == 200
        assert archived.name in returned_names

    async def test_filter_by_name_via_query_param(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_subject(session, name="Findable Route", code="FNDRT201")
        await make_subject(session, name="Other Route", code="OTHRT201")
        headers = await make_auth_header(session, system_admin)

        response = await client.get(
            "/subjects",
            params={"name": "Findable"},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == "Findable Route"

    async def test_pagination_returns_correct_page(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        for i in range(3):
            await make_subject(
                session,
                name=f"Page Subject {i}",
                code=f"PAGE20{i}",
            )

        headers = await make_auth_header(session, system_admin)

        response = await client.get(
            "/subjects",
            params={"skip": 0, "limit": 2},
            headers=headers,
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

        response = await client.get("/subjects", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/subjects")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/subjects", params={"limit": 101}, headers=headers)

        assert response.status_code == 422
