from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.utils.enums import UserStatus
from tests.conftest import make_auth_header
from tests.factories import make_deactivated_user, make_system_admin


class TestDeactivateUser:
    async def test_deactivate_user_returns_204(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/deactivation", headers=headers
        )

        deactivated_user = await UserRepositoryBase.get_user_by_id(session, teacher.id)

        assert response.status_code == 204
        assert deactivated_user.is_active is False
        assert deactivated_user.status == UserStatus.DEACTIVATED

    async def test_deactivate_user_returns_404_when_not_found(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch("/users/999999/deactivation", headers=headers)

        assert response.status_code == 404

    async def test_deactivate_user_returns_409_when_already_inactive(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        deactivated = await make_deactivated_user(session)
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{deactivated.id}/deactivation", headers=headers
        )

        assert response.status_code == 409

    async def test_deactivate_user_returns_404_for_system_admin_target(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        other_admin = await make_system_admin(session)
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{other_admin.id}/deactivation", headers=headers
        )

        assert response.status_code == 404

    async def test_deactivate_user_returns_403_for_non_admin(
        self, session: AsyncSession, client: AsyncClient, teacher: User, student: User
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.patch(
            f"/users/{student.id}/deactivation", headers=headers
        )

        assert response.status_code == 403

    async def test_deactivate_user_returns_401_when_unauthenticated(
        self, client: AsyncClient, teacher: User
    ):
        response = await client.patch(f"/users/{teacher.id}/deactivation")

        assert response.status_code == 401

    async def test_deactivate_user_returns_422_for_invalid_path_id(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch("/users/0/deactivation", headers=headers)

        assert response.status_code == 422
