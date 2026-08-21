from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from tests.conftest import make_auth_header
from tests.factories import make_teacher


class TestUpdateMeCredentials:
    async def test_returns_204_on_username_change(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="creds_username_user")
        headers = await make_auth_header(session, user)

        response = await client.patch(
            "/users/me/credentials",
            json={"username": "int_creds_updated"},
            headers=headers,
        )

        assert response.status_code == 204

    async def test_username_is_actually_changed_in_db(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="creds_db_check_user")
        headers = await make_auth_header(session, user)

        await client.patch(
            "/users/me/credentials",
            json={"username": "creds_db_updated"},
            headers=headers,
        )

        refreshed = await UserRepositoryBase.get_user_by_id(session, user.id)
        assert refreshed.username == "creds_db_updated"

    async def test_old_token_rejected_after_username_change(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="token_invalidate")
        headers = await make_auth_header(session, user)

        await client.patch(
            "/users/me/credentials",
            json={"username": "creds_token_new_name"},
            headers=headers,
        )

        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 401

    async def test_returns_204_on_email_change_request(
        self,
        session: AsyncSession,
        client: AsyncClient,
        mock_send_email_change_verification,
    ):
        user = await make_teacher(session, username="int_creds_email_user")
        headers = await make_auth_header(session, user)

        response = await client.patch(
            "/users/me/credentials",
            json={"email": "int_creds_new@example.com"},
            headers=headers,
        )

        assert response.status_code == 204

    async def test_returns_400_when_no_changes(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)

        response = await client.patch(
            "/users/me/credentials",
            json={"username": teacher.username},
            headers=headers,
        )

        assert response.status_code == 400

    async def test_returns_409_on_duplicate_username(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        existing = await make_teacher(session, username="int_existing_uname")
        user = await make_teacher(session, username="int_conflict_user")
        headers = await make_auth_header(session, user)

        response = await client.patch(
            "/users/me/credentials",
            json={"username": existing.username},
            headers=headers,
        )

        assert response.status_code == 409

    async def test_returns_409_on_duplicate_pending_email(
        self,
        session: AsyncSession,
        client: AsyncClient,
        mock_send_email_change_verification,
    ):
        user = await make_teacher(session, username="int_dup_email_user")
        headers = await make_auth_header(session, user)
        payload = {"email": "int_dup_pending@example.com"}

        await client.patch("/users/me/credentials", json=payload, headers=headers)
        response = await client.patch(
            "/users/me/credentials", json=payload, headers=headers
        )

        assert response.status_code == 409

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.patch(
            "/users/me/credentials", json={"username": "some_name"}
        )

        assert response.status_code == 401

    async def test_invalid_username_too_short_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)
        response = await client.patch(
            "/users/me/credentials",
            json={"username": "ab"},
            headers=headers,
        )

        assert response.status_code == 422
