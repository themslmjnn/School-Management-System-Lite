from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.emails.repository import PendingEmailRepository
from src.users.models.user import User
from src.utils.enums import EmailSendingStatus
from tests.conftest import make_auth_header
from tests.factories import make_email


class TestRetryFailedEmail:
    async def test_resets_failed_email_to_pending(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        email = await make_email(
            session,
            status=EmailSendingStatus.FAILED,
            retry_count=3,
            last_error="Connection refused",
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.post(f"/emails/{email.id}/retry", headers=headers)

        assert response.status_code == 204

        updated = await PendingEmailRepository.get_email_by_id(session, email.id)

        assert updated.status == EmailSendingStatus.PENDING
        assert updated.retry_count == 0
        assert updated.last_error is None

    async def test_returns_404_for_missing_email(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)
        response = await client.post("/emails/999999/retry", headers=headers)

        assert response.status_code == 404

    async def test_forbidden_for_non_admin(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        email = await make_email(session, status=EmailSendingStatus.FAILED)
        headers = await make_auth_header(session, teacher)

        response = await client.post(f"/emails/{email.id}/retry", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, session: AsyncSession
    ):
        email = await make_email(session, status=EmailSendingStatus.FAILED)
        response = await client.post(f"/emails/{email.id}/retry")

        assert response.status_code == 401
