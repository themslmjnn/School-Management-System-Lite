from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import UserStatus
from tests.conftest import make_auth_header
from tests.factories import make_student, make_teacher


class TestGetTeachers:
    async def test_returns_200_with_teachers_only(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        teacher = await make_teacher(session, firstname="Dirteacherone")
        student = await make_student(session, firstname="Dirstudentone")
        headers = await make_auth_header(session, director)

        response = await client.get("/director/users/teachers", headers=headers)

        body = response.json()
        returned_names = {item["firstname"] for item in body["items"]}

        assert response.status_code == 200
        assert teacher.firstname in returned_names
        assert student.firstname not in returned_names

    async def test_filter_by_status_via_query_param(
        self, session: AsyncSession, client: AsyncClient, director: User
    ):
        deactivated = await make_teacher(
            session,
            username="dir_deact_teacher",
            firstname="Dirdeactivatedone",
            status=UserStatus.DEACTIVATED,
            is_active=False,
        )
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/users/teachers",
            params={"status": UserStatus.DEACTIVATED.value},
            headers=headers,
        )

        returned_names = {item["firstname"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert deactivated.firstname in returned_names

    async def test_response_does_not_include_email(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
        teacher: User,
    ):
        headers = await make_auth_header(session, director)

        response = await client.get("/director/users/teachers", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert "email" not in body["items"][0]

    async def test_forbidden_for_system_admin(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get("/director/users/teachers", headers=headers)

        assert response.status_code == 403

    async def test_forbidden_for_teacher(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.get("/director/users/teachers", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/director/users/teachers")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self, session: AsyncSession, client: AsyncClient, director: User
    ):
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/users/teachers", params={"limit": 101}, headers=headers
        )

        assert response.status_code == 422

    async def test_pagination_has_more_field_present(
        self, session: AsyncSession, client: AsyncClient, director: User
    ):
        for i in range(3):
            await make_teacher(session, username=f"paginated_teacher_{i}")

        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/users/teachers",
            params={"skip": 0, "limit": 2},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert body["has_more"] is True
        assert body["total"] == 3
