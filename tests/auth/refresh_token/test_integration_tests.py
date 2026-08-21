from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_teacher


async def _do_login(
    client: AsyncClient,
    username: str,
    password: str = "TestPassword123!",
) -> dict:
    response = await client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    return response


class TestRefreshToken:
    async def test_returns_200_with_new_access_token(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_rt_ok")
        await _do_login(client, user.username)

        response = await client.post("/auth/refresh-token")

        body = response.json()

        assert response.status_code == 200
        assert "access_token" in body

    async def test_rotates_refresh_token_cookie(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_rt_rotate")
        await _do_login(client, user.username)

        old_token = client.cookies.get("refresh_token")

        await client.post("/auth/refresh-token")

        new_token = client.cookies.get("refresh_token")

        assert new_token != old_token

    async def test_returns_401_without_cookie(self, client: AsyncClient):
        response = await client.post("/auth/refresh-token")

        assert response.status_code == 401

    async def test_returns_401_with_only_refresh_token_cookie(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="missing_family")
        await _do_login(client, user.username)

        # Remove the family cookie manually
        client.cookies.delete("refresh_token_family")

        response = await client.post("/auth/refresh-token")

        assert response.status_code == 401

    async def test_reuse_of_consumed_token_returns_401(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_rt_reuse")
        await _do_login(client, user.username)

        old_token = client.cookies.get("refresh_token")
        old_family = client.cookies.get("refresh_token_family")

        # First rotation — valid
        await client.post("/auth/refresh-token")

        # Restore old (now stale) cookies to simulate token reuse
        client.cookies.set("refresh_token", old_token)
        client.cookies.set("refresh_token_family", old_family)

        response = await client.post("/auth/refresh-token")

        assert response.status_code == 401
