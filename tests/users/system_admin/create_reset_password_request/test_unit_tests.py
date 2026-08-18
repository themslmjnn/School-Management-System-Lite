from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.emails.repository import PendingEmailRepository
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.users.services.system_admin import UserServiceAdmin
from src.users.utils.exceptions import (
    UserNotFoundError,
)
from src.utils.enums import EmailType
from tests.factories import make_system_admin


class TestCreateResetPasswordRequest:
    async def test_sets_reset_token_on_session(
        self,
        session: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        await UserServiceAdmin.create_reset_password_request(
            session, system_admin.id, teacher.id
        )

        user_with_session = await UserRepositoryBase.get_user_by_id(
            session, teacher.id, load_session=True
        )
        session = user_with_session.session

        assert session.reset_password_token_hash is not None
        assert session.reset_password_token_expires_at is not None
        assert session.reset_password_token_expires_at > datetime.now(UTC)

    async def test_queues_pending_email_with_correct_fields(
        self,
        session: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        await UserServiceAdmin.create_reset_password_request(
            session, system_admin.id, teacher.id
        )

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            session, system_admin.id
        )
        email = pending_emails[0]

        assert len(pending_emails) == 1
        assert email.recipient == teacher.email
        assert email.subject is not None
        assert email.html_body is not None
        assert email.text_body is not None
        assert email.email_type == EmailType.PASSWORD_RESET_ADMIN
        assert email.triggered_by == system_admin.id
        assert email.recipient_user_id == teacher.id

    async def test_not_found_raises_user_not_found(
        self,
        session: AsyncSession,
        system_admin: User,
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_reset_password_request(
                session, system_admin.id, 999_999
            )

    async def test_excludes_system_admins(
        self,
        session: AsyncSession,
        system_admin: User,
    ):
        other_admin = await make_system_admin(session)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_reset_password_request(
                session, system_admin.id, other_admin.id
            )
