from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.emails.models import EmailType
from src.emails.repository import PendingEmailRepository
from src.users.exceptions.exceptions import (
    DuplicateEmailError,
    MaxStudentsPerEmailError,
    UsernameAlreadyTakenError,
    UserNotFoundError,
)
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from users.schemas.system_admin.user import UpdateUserCredentials
from src.users.services.system_admin.user import UserServiceAdmin
from src.utils.base_exception import NoChangesDetectedError
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.enums import UserStatus
from tests.factories import (
    make_student,
    make_system_admin,
    make_teacher,
)


class TestUpdateUserCredentials:
    async def test_update_username_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        update_request = UpdateUserCredentials(username="newusername1")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, teacher.id, update_request
        )

        updated_user = await UserRepositoryBase.get_user_by_id(test_db, teacher.id)

        assert updated_user.username == "newusername1"

    async def test_update_email_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        update_request = UpdateUserCredentials(email="new.email@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, teacher.id, update_request
        )

        updated_user = await UserRepositoryBase.get_user_by_id(test_db, teacher.id)

        assert updated_user.email == "new.email@example.com"

    async def test_session_always_reset_after_credentials_update(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        update_request = UpdateUserCredentials(username="newusername2")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, teacher.id, update_request
        )

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )
        session = user_with_session.session

        assert session.access_token_version == 2
        assert session.refresh_token_hash is None
        assert session.refresh_token_family is None
        assert session.refresh_token_expires_at is None
        assert session.pending_new_email is None
        assert session.email_change_code_hash is None
        assert session.email_change_code_expires_at is None

    async def test_cache_invalidated_including_token_version(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_delete_cache,
    ):
        update_request = UpdateUserCredentials(username="newusername3")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, teacher.id, update_request
        )

        mock_delete_cache.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(teacher.id),
            UserCacheKey.user_detail_key_staff(teacher.id),
            UserCacheKey.user_detail_key_self(teacher.id),
            SessionCacheKey.access_token_version_key(teacher.id),
        )

    async def test_not_found_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ):
        update_request = UpdateUserCredentials(username="doesntmatter")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user_credentials(
                test_db, system_admin.id, 999_999, update_request
            )

    async def test_excludes_system_admins(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ):
        other_admin = await make_system_admin(test_db)
        update_request = UpdateUserCredentials(username="doesntmatter")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user_credentials(
                test_db, system_admin.id, other_admin.id, update_request
            )

    async def test_no_fields_set_raises_no_changes(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        update_request = UpdateUserCredentials()

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user_credentials(
                test_db, system_admin.id, teacher.id, update_request
            )

    async def test_same_value_raises_no_changes(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        update_request = UpdateUserCredentials(email=teacher.email)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user_credentials(
                test_db, system_admin.id, teacher.id, update_request
            )

    async def test_duplicate_username_raises_error(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        await make_teacher(test_db, username="taken_username")
        update_request = UpdateUserCredentials(username="taken_username")

        with pytest.raises(UsernameAlreadyTakenError):
            await UserServiceAdmin.update_user_credentials(
                test_db, system_admin.id, teacher.id, update_request
            )

    async def test_duplicate_email_non_student_raises_error(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        await make_teacher(test_db, email="taken@example.com")
        update_request = UpdateUserCredentials(email="taken@example.com")

        with pytest.raises(DuplicateEmailError):
            await UserServiceAdmin.update_user_credentials(
                test_db, system_admin.id, teacher.id, update_request
            )


class TestUpdateUserCredentialsStudentEmailLock:
    async def test_student_email_change_acquires_advisory_lock(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
        mock_advisory_lock,
    ):
        update_request = UpdateUserCredentials(email="new.student@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, student.id, update_request
        )

        mock_advisory_lock.assert_called_once_with(
            test_db, phone_number=None, email="new.student@example.com"
        )

    async def test_student_email_unchanged_skips_lock_and_limit(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
        mock_advisory_lock,
        mock_check_contact_limit,
    ):
        update_request = UpdateUserCredentials(email=student.email)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user_credentials(
                test_db, system_admin.id, student.id, update_request
            )

        mock_advisory_lock.assert_not_called()
        mock_check_contact_limit.assert_not_called()

    async def test_non_student_email_change_skips_advisory_lock(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_advisory_lock,
    ):
        update_request = UpdateUserCredentials(email="new.teacher@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, teacher.id, update_request
        )

        mock_advisory_lock.assert_not_called()

    async def test_student_email_contact_limit_reached(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
    ):
        shared_email = "shared@example.com"

        for i in range(3):
            await make_student(
                test_db,
                email=shared_email,
                phone_number=f"+99255511{i:04d}",
                username=f"other_student_{i}",
            )

        update_request = UpdateUserCredentials(email=shared_email)

        with pytest.raises(MaxStudentsPerEmailError):
            await UserServiceAdmin.update_user_credentials(
                test_db, system_admin.id, student.id, update_request
            )


class TestUpdateUserCredentialsActivationReissue:
    async def test_email_change_on_pending_user_reissues_invite_token(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ) -> None:
        pending_user = await make_teacher(
            test_db, status=UserStatus.PENDING_ACTIVATION, is_active=False
        )
        original_hash = (
            await UserRepositoryBase.get_user_by_id(
                test_db, pending_user.id, load_activation=True
            )
        ).activation.invite_token_hash

        update_request = UpdateUserCredentials(email="reissued@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, pending_user.id, update_request
        )

        updated = await UserRepositoryBase.get_user_by_id(
            test_db, pending_user.id, load_activation=True
        )

        assert updated.email == "reissued@example.com"
        assert updated.activation.invite_token_hash is not None
        assert updated.activation.invite_token_hash != original_hash

    async def test_email_change_on_pending_user_queues_invite_email(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ) -> None:
        pending_user = await make_teacher(
            test_db, status=UserStatus.PENDING_ACTIVATION, is_active=False
        )
        update_request = UpdateUserCredentials(email="invite.email@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, pending_user.id, update_request
        )

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
        )

        assert len(pending_emails) == 1
        assert pending_emails[0].email_type == EmailType.INVITE
        assert pending_emails[0].recipient == "invite.email@example.com"
        assert pending_emails[0].recipient_user_id == pending_user.id

    async def test_email_change_on_pending_user_sets_correct_expiry(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ) -> None:
        pending_user = await make_teacher(
            test_db, status=UserStatus.PENDING_ACTIVATION, is_active=False
        )
        update_request = UpdateUserCredentials(email="expiry.check@example.com")

        before_call = datetime.now(UTC)
        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, pending_user.id, update_request
        )
        after_call = datetime.now(UTC)

        updated = await UserRepositoryBase.get_user_by_id(
            test_db, pending_user.id, load_activation=True
        )
        expires_at = updated.activation.invite_token_expires_at

        assert expires_at > before_call
        hours_remaining = (expires_at - after_call).total_seconds() / 3600
        assert abs(hours_remaining - settings.INVITE_TOKEN_EXPIRES_HOURS) < 0.01

    async def test_session_reset_even_when_reissuing_invite(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ) -> None:
        pending_user = await make_teacher(
            test_db, status=UserStatus.PENDING_ACTIVATION, is_active=False
        )
        update_request = UpdateUserCredentials(email="session.reset@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, pending_user.id, update_request
        )

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, pending_user.id, load_session=True
        )
        session = user_with_session.session

        assert session.access_token_version == 2
        assert session.refresh_token_hash is None
        assert session.refresh_token_family is None
        assert session.refresh_token_expires_at is None

    async def test_username_only_change_does_not_reissue_token(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ) -> None:
        pending_user = await make_teacher(
            test_db, status=UserStatus.PENDING_ACTIVATION, is_active=False
        )
        original_hash = (
            await UserRepositoryBase.get_user_by_id(
                test_db, pending_user.id, load_activation=True
            )
        ).activation.invite_token_hash

        update_request = UpdateUserCredentials(username="pending_new_username")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, pending_user.id, update_request
        )

        updated = await UserRepositoryBase.get_user_by_id(
            test_db, pending_user.id, load_activation=True
        )

        assert updated.activation.invite_token_hash == original_hash

    async def test_email_change_on_active_user_does_not_reissue_token(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ) -> None:
        original_hash = (
            await UserRepositoryBase.get_user_by_id(
                test_db, teacher.id, load_activation=True
            )
        ).activation.invite_token_hash

        update_request = UpdateUserCredentials(email="active.change@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, teacher.id, update_request
        )

        updated = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_activation=True
        )

        assert updated.activation.invite_token_hash == original_hash

    async def test_combined_username_and_email_change_on_pending_user(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ) -> None:
        pending_user = await make_teacher(
            test_db, status=UserStatus.PENDING_ACTIVATION, is_active=False
        )
        update_request = UpdateUserCredentials(
            username="combined_username",
            email="combined.new@example.com",
        )

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, pending_user.id, update_request
        )

        updated = await UserRepositoryBase.get_user_by_id(
            test_db, pending_user.id, load_activation=True
        )

        assert updated.username == "combined_username"
        assert updated.email == "combined.new@example.com"
        assert updated.activation.invite_token_hash is not None

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
        )
        assert len(pending_emails) == 1
        assert pending_emails[0].email_type == EmailType.INVITE
        assert pending_emails[0].recipient == "combined.new@example.com"


class TestCredentialsOverrideNotificationEmail:
    async def test_active_user_credentials_change_queues_override_notification(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ) -> None:
        update_request = UpdateUserCredentials(username="override_notif_user")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, teacher.id, update_request
        )

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
        )

        assert len(pending_emails) == 1
        assert pending_emails[0].email_type == EmailType.ADMIN_CREDENTIALS_OVERRIDE
        assert pending_emails[0].recipient_user_id == teacher.id

    async def test_pending_user_email_change_does_not_queue_override_notification(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ) -> None:
        pending_user = await make_teacher(
            test_db, status=UserStatus.PENDING_ACTIVATION, is_active=False
        )
        update_request = UpdateUserCredentials(email="no.override@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, pending_user.id, update_request
        )

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
        )

        email_types = [e.email_type for e in pending_emails]
        assert EmailType.ADMIN_CREDENTIALS_OVERRIDE not in email_types
        assert EmailType.INVITE in email_types
