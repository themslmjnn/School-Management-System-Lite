from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import UserStatus
from tests.conftest import make_auth_header
from tests.factories import make_student, make_teacher


class TestGetTeachers:
    async def test_returns_200_with_staff_only(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)
        teacher = await make_teacher(session, firstname="teacherone")
        student = await make_student(session, firstname="studentone")

        response = await client.get("/users/teachers", headers=headers)

        body = response.json()
        returned_names = {item["firstname"] for item in body["items"]}

        assert response.status_code == 200
        assert teacher.firstname in returned_names
        assert student.firstname not in returned_names

    async def test_filter_by_status_via_query_param(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        deactivated = await make_teacher(
            session,
            status=UserStatus.DEACTIVATED,
            is_active=False,
            firstname="teacherone",
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.get(
            "/users/teachers",
            params={"status": UserStatus.DEACTIVATED.value},
            headers=headers,
        )

        returned_names = {item["firstname"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert deactivated.firstname in returned_names

    async def test_forbidden_for_non_admin(
        self, session: AsyncSession, client: AsyncClient, teacher: User
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.get("/users/teachers", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/users/teachers")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.get(
            "/users/teachers", params={"limit": 101}, headers=headers
        )

        assert response.status_code == 422

    async def test_query_param_cannot_override_role_scoping(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        student = await make_student(session)
        headers = await make_auth_header(session, system_admin)

        response = await client.get(
            "/users/teachers",
            params={"allowed_roles": "SYSTEM_ADMIN"},
            headers=headers,
        )

        returned_roles = {item["id"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert student.id not in returned_roles
        assert system_admin.id not in returned_roles
