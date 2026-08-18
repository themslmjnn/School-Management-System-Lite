from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.emails.models import PendingEmail
from src.users.models.user import User
from src.utils.enums import UserRole, UserStatus
from tests.conftest import make_auth_header
from tests.factories import (
    make_system_admin,
    make_teacher,
    make_user,
)


async def _get_pending_email_for(db, recipient_user_id: int) -> PendingEmail:
    query = select(PendingEmail).where(
        PendingEmail.recipient_user_id == recipient_user_id
    )

    result = await db.execute(query)

    return result.scalar_one()


class TestResendActivationInvite:
    async def test_system_admin_resends_invite_returns_204(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        target = await make_user(
            session, role=UserRole.TEACHER, status=UserStatus.PENDING_ACTIVATION
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            f"/users/{target.id}/resend-invite",
            headers=headers,
        )

        assert response.status_code == 204
        assert response.content == b""

        pending_email = await _get_pending_email_for(session, target.id)
        assert pending_email.recipient == target.email

    async def test_nonexistent_target_returns_404(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        headers = await make_auth_header(session, system_admin)

        response = await client.post("/users/999999999/resend-invite", headers=headers)

        assert response.status_code == 404

    async def test_system_admin_target_returns_404(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        other_admin = await make_system_admin(
            session, status=UserStatus.PENDING_ACTIVATION
        )
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            f"/users/{other_admin.id}/resend-invite",
            headers=headers,
        )

        assert response.status_code == 404

    async def test_target_not_pending_activation_returns_404(
        self, session: AsyncSession, client: AsyncClient, system_admin: User
    ):
        active_target = await make_teacher(session, status=UserStatus.ACTIVE)
        headers = await make_auth_header(session, system_admin)

        response = await client.post(
            f"/users/{active_target.id}/resend-invite",
            headers=headers,
        )

        assert response.status_code == 409

    async def test_non_admin_caller_forbidden(
        self, session: AsyncSession, client: AsyncClient, teacher: User
    ):
        target = await make_user(
            session, role=UserRole.STUDENT, status=UserStatus.PENDING_ACTIVATION
        )
        headers = await make_auth_header(session, teacher)

        response = await client.post(
            f"/users/{target.id}/resend-invite",
            headers=headers,
        )

        assert response.status_code == 403

    async def test_unauthenticated_caller_returns_401(
        self, session: AsyncSession, client: AsyncClient
    ):
        target = await make_user(
            session, role=UserRole.STUDENT, status=UserStatus.PENDING_ACTIVATION
        )

        response = await client.post(f"/users/{target.id}/resend-invite")

        assert response.status_code == 401
