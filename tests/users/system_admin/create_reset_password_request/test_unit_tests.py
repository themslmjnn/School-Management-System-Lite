from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import CurrentUser
from src.emails.repository import PendingEmailRepository
from src.users.exceptions.exceptions import (
    UserNotFoundError,
)
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.users.services.system_admin.user import UserServiceAdmin
from src.utils.enums import EmailType, UserRole
from tests.factories import make_system_admin


class TestCreateResetPasswordRequest:
    async def test_sets_reset_token_on_session(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        current_user = CurrentUser(id=system_admin.id, role=UserRole.SYSTEM_ADMIN)

        await UserServiceAdmin.create_reset_password_request(
            test_db, current_user, teacher.id
        )

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )
        session = user_with_session.session

        assert session.reset_password_token_hash is not None
        assert session.reset_password_token_expires_at is not None
        assert session.reset_password_token_expires_at > datetime.now(UTC)

    async def test_queues_pending_email_with_correct_fields(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        current_user = CurrentUser(id=system_admin.id, role=UserRole.SYSTEM_ADMIN)

        await UserServiceAdmin.create_reset_password_request(
            test_db, current_user, teacher.id
        )

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
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
        test_db: AsyncSession,
        system_admin: User,
    ):
        current_user = CurrentUser(id=system_admin.id, role=UserRole.SYSTEM_ADMIN)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_reset_password_request(
                test_db, current_user, 999_999
            )

    async def test_excludes_system_admins(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ):
        other_admin = await make_system_admin(test_db)
        current_user = CurrentUser(id=system_admin.id, role=UserRole.SYSTEM_ADMIN)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_reset_password_request(
                test_db, current_user, other_admin.id
            )
