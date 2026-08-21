from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import generate_email_change_code
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from tests.conftest import make_auth_header
from tests.factories import make_teacher


class TestConfirmEmailChange:
    async def _setup_pending_change(
        self,
        session: AsyncSession,
        user,
        new_email: str,
        minutes_until_expiry: int = 15,
    ) -> str:
        raw_code, hashed_code = generate_email_change_code()

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        u.session.pending_new_email = new_email
        u.session.email_change_code_hash = hashed_code
        u.session.email_change_code_expires_at = datetime.now(UTC) + timedelta(
            minutes=minutes_until_expiry
        )
        await session.commit()

        return raw_code

    async def test_returns_204_on_valid_code(
        self,
        session: AsyncSession,
        client: AsyncClient,
        mock_send_email_changed_notification,
    ):
        user = await make_teacher(session, username="confirm_email")
        headers = await make_auth_header(session, user)
        raw_code = await self._setup_pending_change(
            session, user, "int_confirmed@example.com"
        )

        response = await client.post(
            "/users/me/credentials/confirm-email",
            json={"code": raw_code},
            headers=headers,
        )

        assert response.status_code == 204

    async def test_email_is_updated_in_db(
        self,
        session: AsyncSession,
        client: AsyncClient,
        mock_send_email_changed_notification,
    ):
        user = await make_teacher(session, username="confirm_db_teacher")
        headers = await make_auth_header(session, user)
        new_email = "int_db_confirmed@example.com"
        raw_code = await self._setup_pending_change(session, user, new_email)

        await client.post(
            "/users/me/credentials/confirm-email",
            json={"code": raw_code},
            headers=headers,
        )

        refreshed = await UserRepositoryBase.get_user_by_id(session, user.id)
        assert refreshed.email == new_email

    async def test_old_token_invalid_after_email_confirm(
        self,
        session: AsyncSession,
        client: AsyncClient,
        mock_send_email_changed_notification,
    ):
        user = await make_teacher(session, username="confirm_token")
        headers = await make_auth_header(session, user)
        raw_code = await self._setup_pending_change(
            session, user, "int_token_confirmed@example.com"
        )

        await client.post(
            "/users/me/credentials/confirm-email",
            json={"code": raw_code},
            headers=headers,
        )

        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 401

    async def test_returns_404_when_no_pending_change(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)
        response = await client.post(
            "/users/me/credentials/confirm-email",
            json={"code": "123456"},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_returns_400_on_expired_code(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="confirm_expired")
        headers = await make_auth_header(session, user)
        raw_code = await self._setup_pending_change(
            session, user, "int_expired@example.com", minutes_until_expiry=-1
        )

        response = await client.post(
            "/users/me/credentials/confirm-email",
            json={"code": raw_code},
            headers=headers,
        )

        assert response.status_code == 400

    async def test_returns_400_on_wrong_code(
        self,
        session: AsyncSession,
        client: AsyncClient,
    ):
        user = await make_teacher(session, username="confirm_wrong")
        headers = await make_auth_header(session, user)
        await self._setup_pending_change(session, user, "int_wrong_code@example.com")

        response = await client.post(
            "/users/me/credentials/confirm-email",
            json={"code": "000000"},
            headers=headers,
        )

        assert response.status_code == 400

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/users/me/credentials/confirm-email", json={"code": "123456"}
        )

        assert response.status_code == 401
