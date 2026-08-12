from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import verify_invite_token
from src.emails.models import EmailType, PendingEmail
from users.utils.exceptions import (
    UserNotFoundError,
    UserNotPendingActivationError,
)
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from users.services.system_admin import UserServiceAdmin
from src.utils.enums import UserRole, UserStatus
from tests.factories import (
    make_system_admin,
    make_teacher,
    make_user,
)


def _extract_raw_token_from_text_body(text_body: str) -> str:
    for line in text_body.splitlines():
        if "token=" in line:
            query = parse_qs(urlparse(line.strip()).query)
            return query["token"][0]

    raise AssertionError("No activation link with a token= param found in text_body")


async def _get_pending_email_for(db, recipient_user_id: int) -> PendingEmail:
    result = await db.execute(
        select(PendingEmail).where(PendingEmail.recipient_user_id == recipient_user_id)
    )

    return result.scalar_one()


class TestResendActivationInvite:
    async def test_resends_invite_and_persists_matching_token(
        self, test_db: AsyncSession, system_admin: User
    ):
        target = await make_user(
            test_db,
            role=UserRole.TEACHER,
            status=UserStatus.PENDING_ACTIVATION,
        )
        target = await UserRepositoryBase.get_user_by_id(
            test_db, target.id, load_activation=True
        )
        original_hash = target.activation.invite_token_hash

        await UserServiceAdmin.resend_activation_invite(
            test_db, system_admin.id, target.id
        )

        updated_target = await UserRepositoryBase.get_user_by_id(
            test_db, target.id, load_activation=True
        )
        assert updated_target.activation.invite_token_hash != original_hash

        pending_email = await _get_pending_email_for(test_db, target.id)
        assert pending_email.recipient == target.email
        assert pending_email.email_type == EmailType.INVITE
        assert pending_email.triggered_by == system_admin.id
        assert pending_email.recipient_user_id == target.id

        raw_token = _extract_raw_token_from_text_body(pending_email.text_body)
        assert verify_invite_token(
            raw_token, updated_target.activation.invite_token_hash
        )

    async def test_new_expiry_is_settings_window_from_now(
        self, test_db: AsyncSession, system_admin: User
    ):
        target = await make_user(
            test_db, role=UserRole.STUDENT, status=UserStatus.PENDING_ACTIVATION
        )

        before_call = datetime.now(UTC)
        await UserServiceAdmin.resend_activation_invite(
            test_db, system_admin.id, target.id
        )
        after_call = datetime.now(UTC)

        updated_target = await UserRepositoryBase.get_user_by_id(
            test_db, target.id, load_activation=True
        )
        before_call + settings.INVITE_TOKEN_EXPIRES_HOURS_delta if False else None

        expires_at = updated_target.activation.invite_token_expires_at
        assert expires_at > before_call

        hours_delta = (expires_at - after_call).total_seconds() / 3600
        assert abs(hours_delta - settings.INVITE_TOKEN_EXPIRES_HOURS) < 0.01

    async def test_target_user_not_found_raises(
        self, test_db: AsyncSession, system_admin: User
    ):
        nonexistent_id = 999_999_999

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.resend_activation_invite(
                test_db, system_admin.id, nonexistent_id
            )

    async def test_target_role_excluded_from_system_admin_raises_not_found(
        self, test_db: AsyncSession, system_admin: User
    ):
        other_admin = await make_system_admin(
            test_db, status=UserStatus.PENDING_ACTIVATION
        )

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.resend_activation_invite(
                test_db, system_admin.id, other_admin.id
            )

    async def test_target_not_pending_activation_raises(
        self, test_db: AsyncSession, system_admin: User
    ):
        active_target = await make_teacher(test_db, status=UserStatus.ACTIVE)

        with pytest.raises(UserNotPendingActivationError):
            await UserServiceAdmin.resend_activation_invite(
                test_db, system_admin.id, active_target.id
            )

    async def test_deactivated_target_raises_not_pending(
        self, test_db: AsyncSession, system_admin: User
    ):
        deactivated_target = await make_user(
            test_db,
            role=UserRole.GUARDIAN,
            status=UserStatus.DEACTIVATED,
            is_active=False,
        )

        with pytest.raises(UserNotPendingActivationError):
            await UserServiceAdmin.resend_activation_invite(
                test_db, system_admin.id, deactivated_target.id
            )
