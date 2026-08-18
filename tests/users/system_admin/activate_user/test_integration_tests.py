from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from tests.conftest import make_auth_header
from tests.factories import make_deactivated_user


class TestActivateUser:
    async def test_activate_user_returns_204(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        deactivated = await make_deactivated_user(session)
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{deactivated.id}/activation", headers=headers
        )

        activated = await UserRepositoryBase.get_user_by_id(
            session, deactivated.id, load_login_lockout=True
        )

        assert response.status_code == 204
        assert activated.is_active is True
        assert activated.login_lockout.failed_login_attempts == 0
        assert activated.login_lockout.locked_until is None

    async def test_activate_user_returns_404_when_not_found(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch("/users/999999/activation", headers=headers)

        assert response.status_code == 404

    async def test_activate_user_returns_409_when_already_active(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch(
            f"/users/{teacher.id}/activation", headers=headers
        )

        assert response.status_code == 409

    async def test_activate_user_returns_403_for_non_admin(
        self, session: AsyncSession, client: AsyncClient, teacher: User
    ):
        deactivated = await make_deactivated_user(session)
        headers = await make_auth_header(session, teacher)

        response = await client.patch(
            f"/users/{deactivated.id}/activation", headers=headers
        )

        assert response.status_code == 403

    async def test_activate_user_returns_401_when_unauthenticated(
        self, client: AsyncClient
    ):
        deactivated_id = 1
        response = await client.patch(f"/users/{deactivated_id}/activation")

        assert response.status_code == 401

    async def test_activate_user_returns_422_for_invalid_path_id(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.patch("/users/0/activation", headers=headers)

        assert response.status_code == 422
