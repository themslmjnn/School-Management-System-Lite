from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.utils.enums import EmailSendingStatus, EmailType
from tests.conftest import make_auth_header
from tests.factories import make_email


class TestGetEmails:
    async def test_returns_200_with_all_emails(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_email(session, status=EmailSendingStatus.FAILED)
        await make_email(session, status=EmailSendingStatus.SENT)
        await make_email(session, status=EmailSendingStatus.PENDING)

        headers = await make_auth_header(session, system_admin)
        response = await client.get("/emails", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["total"] == 3

    async def test_filter_by_failed_status(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_email(session, status=EmailSendingStatus.FAILED)
        await make_email(session, status=EmailSendingStatus.SENT)

        headers = await make_auth_header(session, system_admin)
        response = await client.get(
            "/emails",
            params={"status": EmailSendingStatus.FAILED.value},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert body["total"] == 1
        assert body["items"][0]["status"] == EmailSendingStatus.FAILED.value

    async def test_filter_by_sent_status(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_email(session, status=EmailSendingStatus.SENT)
        await make_email(session, status=EmailSendingStatus.FAILED)

        headers = await make_auth_header(session, system_admin)
        response = await client.get(
            "/emails",
            params={"status": EmailSendingStatus.SENT.value},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert body["total"] == 1
        assert body["items"][0]["status"] == EmailSendingStatus.SENT.value

    async def test_filter_by_email_type(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_email(session, email_type=EmailType.INVITE)
        await make_email(session, email_type=EmailType.FORGOT_PASSWORD)

        headers = await make_auth_header(session, system_admin)
        response = await client.get(
            "/emails",
            params={"email_type": EmailType.INVITE.value},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert body["total"] == 1
        assert body["items"][0]["email_type"] == EmailType.INVITE.value

    async def test_filter_by_triggered_by(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_email(session, triggered_by=system_admin.id)
        await make_email(session)

        headers = await make_auth_header(session, system_admin)
        response = await client.get(
            "/emails",
            params={"triggered_by": system_admin.id},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert body["total"] == 1
        assert body["items"][0]["triggered_by"] == system_admin.id

    async def test_filter_by_recipient_user_id(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
        teacher: User,
    ):
        await make_email(session, recipient_user_id=teacher.id)
        await make_email(session)

        headers = await make_auth_header(session, system_admin)
        response = await client.get(
            "/emails",
            params={"recipient_user_id": teacher.id},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert body["total"] == 1
        assert body["items"][0]["recipient_user_id"] == teacher.id

    async def test_pagination_returns_correct_page(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        for _ in range(5):
            await make_email(session)

        headers = await make_auth_header(session, system_admin)
        response = await client.get(
            "/emails",
            params={"skip": 0, "limit": 3},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert len(body["items"]) == 3
        assert body["total"] == 5
        assert body["has_more"] is True

    async def test_has_more_false_on_last_page(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        for _ in range(3):
            await make_email(session)

        headers = await make_auth_header(session, system_admin)
        response = await client.get(
            "/emails",
            params={"skip": 2, "limit": 2},
            headers=headers,
        )

        body = response.json()

        assert response.status_code == 200
        assert body["has_more"] is False

    async def test_returns_empty_list_when_no_emails(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)
        response = await client.get("/emails", headers=headers)

        body = response.json()

        assert response.status_code == 200
        assert body["total"] == 0
        assert body["items"] == []

    async def test_forbidden_for_non_admin(
        self,
        session: AsyncSession,
        client: AsyncClient,
        teacher: User,
    ):
        headers = await make_auth_header(session, teacher)
        response = await client.get("/emails", headers=headers)

        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.get("/emails")

        assert response.status_code == 401

    async def test_limit_exceeding_max_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)
        response = await client.get("/emails", params={"limit": 101}, headers=headers)

        assert response.status_code == 422

    async def test_invalid_status_value_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)
        response = await client.get(
            "/emails", params={"status": "not_a_real_status"}, headers=headers
        )

        assert response.status_code == 422

    async def test_invalid_email_type_value_returns_422(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        headers = await make_auth_header(session, system_admin)
        response = await client.get(
            "/emails",
            params={"email_type": "not_a_real_type"},
            headers=headers,
        )

        assert response.status_code == 422

    async def test_response_contains_expected_fields(
        self,
        session: AsyncSession,
        client: AsyncClient,
        system_admin: User,
    ):
        await make_email(session)

        headers = await make_auth_header(session, system_admin)
        response = await client.get("/emails", headers=headers)

        item = response.json()["items"][0]

        assert "id" in item
        assert "recipient" in item
        assert "subject" in item
        assert "email_type" in item
        assert "status" in item
        assert "retry_count" in item
        assert "last_error" in item
        assert "sent_at" in item
        assert "created_at" in item
        assert "triggered_by" in item
        assert "recipient_user_id" in item
