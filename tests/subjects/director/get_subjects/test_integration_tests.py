from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from tests.conftest import make_auth_header
from tests.factories import make_subject


class TestDirectorGetSubjectsEndpoint:
    async def test_returns_200_with_active_subjects_only(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        subject = await make_subject(
            session, name="Dir Route Subject", code="DIRRTE201"
        )
        await make_subject(
            session,
            name="Dir Archived Route",
            code="DIRRARCH201",
            is_archived=True,
        )
        headers = await make_auth_header(session, director)

        response = await client.get("/director/subjects", headers=headers)

        body = response.json()
        returned_names = {item["name"] for item in body["items"]}

        assert response.status_code == 200
        assert subject.name in returned_names
        assert "Dir Archived Route" not in returned_names

    async def test_include_archived_param_ignored(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        await make_subject(session, name="Dir Active QP", code="DIRACQP201")
        archived = await make_subject(
            session,
            name="Dir Archived QP",
            code="DIRARCHQP201",
            is_archived=True,
        )
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/subjects",
            params={"include_archived": True},
            headers=headers,
        )

        body = response.json()
        returned_names = {item["name"] for item in body["items"]}

        assert response.status_code == 200
        assert archived.name not in returned_names

    async def test_filter_by_name_via_query_param(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        await make_subject(session, name="Dir Findable Route", code="DIRFNDRT201")
        await make_subject(session, name="Dir Other Route", code="DIROTHRT201")
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/subjects",
            params={"name": "Findable"},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == "Dir Findable Route"

    async def test_response_does_not_include_archived_at(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        await make_subject(session, name="Dir Schema Check", code="DIRSCHK201")
        headers = await make_auth_header(session, director)

        response = await client.get("/director/subjects", headers=headers)

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

        response = await client.get("/director/subjects", headers=headers)

        assert response.status_code == 403

    async def test_forbidden_for_teacher(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.get("/director/subjects", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/director/subjects")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/subjects", params={"limit": 101}, headers=headers
        )

        assert response.status_code == 422
