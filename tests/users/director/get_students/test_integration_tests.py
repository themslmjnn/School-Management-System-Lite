from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import UserStatus
from tests.conftest import make_auth_header
from tests.factories import make_group, make_student, make_teacher


class TestGetStudents:
    async def test_returns_200_with_students_only(
        self,
        session: AsyncSession,
        client: AsyncClient,
        director: User,
    ):
        student = await make_student(session, firstname="Studentone")
        teacher = await make_teacher(session, firstname="Teacherone")
        headers = await make_auth_header(session, director)

        response = await client.get("/director/users/students", headers=headers)

        body = response.json()
        returned_names = {item["firstname"] for item in body["items"]}

        assert response.status_code == 200
        assert student.firstname in returned_names
        assert teacher.firstname not in returned_names
        assert "email" not in response.json()["items"][0]

    async def test_filter_by_status_via_query_param(
        self, session: AsyncSession, client: AsyncClient, director: User
    ):
        deactivated = await make_student(
            session,
            username="deactivated_student",
            firstname="Deactivatedone",
            status=UserStatus.DEACTIVATED,
            is_active=False,
        )
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/users/students",
            params={"status": UserStatus.DEACTIVATED.value},
            headers=headers,
        )

        returned_names = {item["firstname"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert deactivated.firstname in returned_names

    async def test_filter_by_group_id_via_query_param(
        self, session: AsyncSession, client: AsyncClient, director: User
    ):
        group = await make_group(session)
        in_group = await make_student(
            session,
            username="in_group_student",
            firstname="Ingroupone",
            group_id=group.id,
        )
        await make_student(session, username="no_group_student")
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/users/students",
            params={"group_id": group.id},
            headers=headers,
        )

        returned_names = {item["firstname"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert in_group.firstname in returned_names
        assert len(returned_names) == 1

    async def test_group_field_present_in_response(
        self, session: AsyncSession, client: AsyncClient, director: User
    ):
        await make_student(session, username="no_group_check")
        headers = await make_auth_header(session, director)

        response = await client.get("/director/users/students", headers=headers)

        body = response.json()

        assert "group" in body["items"][0]

    async def test_forbidden_for_non_admin(
        self, session: AsyncSession, client: AsyncClient, teacher: User
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.get("/director/users/students", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/director/users/students")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self, session: AsyncSession, client: AsyncClient, director: User
    ):
        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/users/students", params={"limit": 101}, headers=headers
        )

        assert response.status_code == 422

    async def test_pagination_returns_correct_page(
        self, session: AsyncSession, client: AsyncClient, director: User
    ):
        for i in range(3):
            await make_student(session, username=f"paginated_student_{i}")

        headers = await make_auth_header(session, director)

        response = await client.get(
            "/director/users/students", params={"skip": 0, "limit": 2}, headers=headers
        )

        body = response.json()

        assert response.status_code == 200
        assert len(body["items"]) == 2
        assert body["total"] == 3
        assert body["has_more"] is True
