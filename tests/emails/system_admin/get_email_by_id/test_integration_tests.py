from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import EmailSendingStatus
from tests.conftest import make_auth_header
from tests.factories import make_email


class TestGetEmailById:
    async def test_returns_200_with_correct_data(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        email = await make_email(session, status=EmailSendingStatus.FAILED)
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/emails/{email.id}", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["id"] == email.id
        assert body["recipient"] == email.recipient
        assert body["status"] == EmailSendingStatus.FAILED.value

    async def test_returns_404_when_not_found(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)
        response = await client.get("/emails/999999", headers=headers)

        assert response.status_code == 404

    async def test_forbidden_for_non_admin(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        email = await make_email(session)
        headers = await make_auth_header(session, teacher)

        response = await client.get(f"/emails/{email.id}", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, session: AsyncSession
    ):
        email = await make_email(session)
        response = await client.get(f"/emails/{email.id}")

        assert response.status_code == 401

    async def test_invalid_path_id_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)
        response = await client.get("/emails/0", headers=headers)

        assert response.status_code == 422

    async def test_response_contains_detailed_fields(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        email = await make_email(session, retry_count=2, last_error="SMTP timeout")
        headers = await make_auth_header(session, system_admin)

        response = await client.get(f"/emails/{email.id}", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["retry_count"] == 2
        assert body["last_error"] == "SMTP timeout"
        assert "created_at" in body
