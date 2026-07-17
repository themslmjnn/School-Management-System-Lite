from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import UserStatus
from tests.conftest import make_auth_header
from tests.factories import make_student, make_teacher


class TestGetStaffEndpoint:
    async def test_returns_200_with_staff_only(
        self,
        test_db: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
        vice_director: User,
        student: User,
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get("/users/staff", headers=headers)

        body = response.json()
        returned_roles = {item["role"] for item in body["items"]}

        assert response.status_code == 200
        assert teacher.role in returned_roles
        assert vice_director.role in returned_roles
        assert student.role not in returned_roles

    async def test_filter_by_status_via_query_param(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        deactivated = await make_teacher(
            test_db, status=UserStatus.DEACTIVATED, is_active=False
        )
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get(
            "/users/staff",
            params={"status": UserStatus.DEACTIVATED.value},
            headers=headers,
        )

        returned_roles = {item["role"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert deactivated.role in returned_roles

    async def test_forbidden_for_non_admin(
        self, test_db: AsyncSession, client: AsyncClient, teacher: User
    ):
        headers = await make_auth_header(test_db, teacher)

        response = await client.get("/users/staff", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/users/staff")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get(
            "/users/staff", params={"limit": 101}, headers=headers
        )

        assert response.status_code == 422

    async def test_query_param_cannot_override_role_scoping(
        self, test_db: AsyncSession, client: AsyncClient, system_admin: User
    ):
        student = await make_student(test_db)
        headers = await make_auth_header(test_db, system_admin)

        response = await client.get(
            "/users/staff",
            params={"allowed_roles": "SYSTEM_ADMIN"},
            headers=headers,
        )

        returned_roles = {item["id"] for item in response.json()["items"]}

        assert response.status_code == 200
        assert student.id not in returned_roles
        assert system_admin.id not in returned_roles
