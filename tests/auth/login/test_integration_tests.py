from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.enums import UserStatus
from tests.factories import make_deactivated_user, make_teacher


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


class TestLogin:
    async def test_returns_200_and_access_token(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_login_ok")

        response = await _do_login(client, user.username)

        body = response.json()

        assert response.status_code == 200
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_sets_refresh_token_cookies(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_cookie_user")

        await _do_login(client, user.username)

        assert "refresh_token" in client.cookies
        assert "refresh_token_family" in client.cookies

    async def test_returns_401_for_wrong_password(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="int_wrong_pwd")

        response = await _do_login(client, user.username, password="WrongPassword!")

        assert response.status_code == 401

    async def test_returns_401_for_unknown_user(self, client: AsyncClient):
        response = await _do_login(client, "nobody_at_all")

        assert response.status_code == 401

    async def test_returns_401_for_pending_activation(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(
            session,
            username="int_pending_user",
            status=UserStatus.PENDING_ACTIVATION,
            is_active=False,
        )

        response = await _do_login(client, user.username)

        assert response.status_code == 401

    async def test_returns_409_for_deactivated_user(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_deactivated_user(session, username="deactivated_login")

        response = await _do_login(client, user.username)

        assert response.status_code == 409

    async def test_returns_403_for_locked_account(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        locked_until = datetime.now(UTC) + timedelta(minutes=10)
        user = await make_teacher(
            session,
            username="int_locked_user",
            locked_until=locked_until,
        )

        response = await _do_login(client, user.username)

        assert response.status_code == 403

    async def test_missing_credentials_returns_422(self, client: AsyncClient):
        response = await client.post("/auth/login", data={})

        assert response.status_code == 422
