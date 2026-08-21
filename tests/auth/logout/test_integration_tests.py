from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from tests.conftest import make_auth_header


class TestLogout:
    async def test_returns_204_on_success(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.post("/auth/logout", headers=headers)

        assert response.status_code == 204

    async def test_invalidates_session_after_logout(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)
        await client.post("/auth/logout", headers=headers)

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, teacher.id, load_session=True
        )

        assert refreshed.session.refresh_token_hash is None

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.post("/auth/logout")

        assert response.status_code == 401
