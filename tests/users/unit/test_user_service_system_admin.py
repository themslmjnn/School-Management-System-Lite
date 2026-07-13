import asyncio
from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import CurrentUser
from core.security import verify_invite_token
from src.core.config import settings
from src.emails.models import EmailType, PendingEmail
from src.emails.repository import PendingEmailRepository
from src.users.models.users import User
from src.users.repositories.users import UserRepositoryBase
from src.users.schemas.users import (
    CreateGuardianAdmin,
    CreateStaffAdmin,
    CreateStudentAdmin,
    UpdateStaffAndGuardianAdmin,
    UpdateStudentAdmin,
    UpdateUserCredentials,
)
from src.users.services.system_admin import UserServiceAdmin
from src.utils.enums import UserRole, UserStatus
from src.utils.exceptions import (
    CannotCreateDirectorError,
    CannotCreateSystemAdminError,
    DuplicateEmailError,
    DuplicatePhoneNumberError,
    MaxStaffOrGuardianPerEmailError,
    MaxStaffOrGuardianPerPhoneNumberError,
    MaxStudentsPerEmailError,
    MaxStudentsPerPhoneNumberError,
    NoChangesDetectedError,
    UserAlreadyActiveError,
    UserAlreadyInactiveError,
    UserAlreadyPendingDeletionError,
    UsernameAlreadyTakenError,
    UserNotFoundError,
    UserNotPendingActivationError,
)
from tests.factories import (
    make_deactivated_user,
    make_guardian,
    make_student,
    make_system_admin,
    make_teacher,
    make_user,
)
from utils.cache_keys import SessionCacheKey, UserCacheKey


class TestRegisterStaff:
    async def test_block_system_admin_creation(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        valid_create_staff_request.role = UserRole.SYSTEM_ADMIN

        with pytest.raises(CannotCreateSystemAdminError):
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_staff_request
            )

    async def test_block_director_creation(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        valid_create_staff_request.role = UserRole.DIRECTOR

        with pytest.raises(CannotCreateDirectorError):
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_staff_request
            )

    @pytest.mark.parametrize(
        ("existing_user_data", "request_override", "expected_exception"),
        [
            (
                {"username": "taken_username"},
                {"username": "taken_username"},
                UsernameAlreadyTakenError,
            ),
            (
                {"email": "taken@example.com"},
                {"email": "taken@example.com"},
                MaxStaffOrGuardianPerEmailError,
            ),
            (
                {"phone_number": "+992555111222"},
                {"phone_number": "+992555111222"},
                MaxStaffOrGuardianPerPhoneNumberError,
            ),
        ],
    )
    async def test_reject_duplicate_fields(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
        existing_user_data: dict,
        request_override: dict,
        expected_exception,
    ):
        await make_teacher(test_db, **existing_user_data)

        for field, value in request_override.items():
            setattr(valid_create_staff_request, field, value)

        with pytest.raises(expected_exception):
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_staff_request
            )

    async def test_create_user_session_table_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_staff_request
        )

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, user.id, load_session=True
        )
        session = user_with_session.session

        assert session.id is not None
        assert session.user_id == user.id
        assert session.access_token_version == 1
        assert session.refresh_token_hash is None
        assert session.refresh_token_expires_at is None
        assert session.refresh_token_family is None
        assert session.reset_password_token_hash is None
        assert session.reset_password_token_expires_at is None
        assert session.pending_new_email is None
        assert session.email_change_code_hash is None
        assert session.email_change_code_expires_at is None

    async def test_create_user_login_lockout_table_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_staff_request
        )

        user_with_lockout = await UserRepositoryBase.get_user_by_id(
            test_db, user.id, load_login_lockout=True
        )
        lockout = user_with_lockout.login_lockout

        assert lockout.id is not None
        assert lockout.user_id == user.id
        assert lockout.failed_login_attempts == 0
        assert lockout.locked_until is None

    async def test_create_user_activation_table_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_staff_request
        )

        user_with_activation = await UserRepositoryBase.get_user_by_id(
            test_db, user.id, load_activation=True
        )
        activation = user_with_activation.activation

        assert activation.id is not None
        assert activation.user_id == user.id
        assert activation.invite_token_hash is not None
        assert activation.invite_token_expires_at is not None
        assert activation.invite_token_expires_at > datetime.now(UTC)

    async def test_create_pending_email_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_staff_request
        )

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
        )
        email = pending_emails[0]

        assert len(pending_emails) == 1
        assert email.recipient == user.email
        assert email.subject is not None
        assert email.html_body is not None
        assert email.text_body is not None
        assert email.email_type == EmailType.INVITE
        assert email.triggered_by == system_admin.id
        assert email.recipient_user_id == user.id

    async def test_create_user_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_staff_request
        )

        assert user.id is not None
        assert user.email == valid_create_staff_request.email
        assert user.role == valid_create_staff_request.role
        assert user.status == UserStatus.PENDING_ACTIVATION
        assert user.is_active is False
        assert user.password_hash is None
        assert user.date_of_birth is None
        assert user.address is None
        assert user.created_by == system_admin.id

    @pytest.mark.db_constraint
    @pytest.mark.parametrize(
        "field, existing_kwargs, duplicate_value, expected_exception",
        [
            (
                "email",
                {
                    "email": "constraint.check@example.com",
                    "phone_number": "+992555111333",
                },
                "constraint.check@example.com",
                DuplicateEmailError,
            ),
            (
                "phone_number",
                {
                    "email": "constraint.check@example.com",
                    "phone_number": "+992555111333",
                },
                "+992555111333",
                DuplicatePhoneNumberError,
            ),
        ],
    )
    async def test_contact_limit_db_constraint_catches_bypassed_precheck(
        self,
        field,
        existing_kwargs,
        duplicate_value,
        expected_exception,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
        mocker,
    ):
        await make_teacher(test_db, **existing_kwargs)

        mocker.patch(
            "src.users.services.system_admin.UserRepositoryBase.count_users_with_contact",
            return_value=0,
        )

        setattr(valid_create_staff_request, field, duplicate_value)

        with pytest.raises(expected_exception):
            await UserServiceAdmin.register_user(
                test_db,
                system_admin.id,
                valid_create_staff_request,
            )


class TestRegisterStudent:
    @pytest.mark.parametrize(
        ("existing_user_data", "request_override", "expected_exception"),
        [
            (
                {"username": "taken_username"},
                {"username": "taken_username"},
                UsernameAlreadyTakenError,
            ),
        ],
    )
    async def test_reject_duplicate_username(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
        existing_user_data: dict,
        request_override: dict,
        expected_exception,
    ):
        await make_teacher(test_db, **existing_user_data)

        for field, value in request_override.items():
            setattr(valid_create_student_request, field, value)

        with pytest.raises(expected_exception):
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_student_request
            )

    @pytest.mark.parametrize(
        ("field", "value", "expected_exception"),
        [
            ("email", "shared@example.com", MaxStudentsPerEmailError),
            ("phone_number", "+992555333444", MaxStudentsPerPhoneNumberError),
        ],
    )
    async def test_reject_when_student_contact_limit_reached(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
        field,
        value,
        expected_exception,
    ):
        for i in range(3):
            await make_student(
                test_db,
                username=f"existing_student_{i}",
                **{field: value},
            )

        setattr(valid_create_student_request, field, value)

        with pytest.raises(expected_exception):
            await UserServiceAdmin.register_user(
                test_db,
                system_admin.id,
                valid_create_student_request,
            )

    async def test_create_user_session_table_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_student_request
        )

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, user.id, load_session=True
        )
        session = user_with_session.session

        assert session.id is not None
        assert session.user_id == user.id
        assert session.access_token_version == 1
        assert session.refresh_token_hash is None

    async def test_create_user_login_lockout_table_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_student_request
        )

        user_with_lockout = await UserRepositoryBase.get_user_by_id(
            test_db, user.id, load_login_lockout=True
        )
        lockout = user_with_lockout.login_lockout

        assert lockout.failed_login_attempts == 0
        assert lockout.locked_until is None

    async def test_create_user_activation_table_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_student_request
        )

        user_with_activation = await UserRepositoryBase.get_user_by_id(
            test_db, user.id, load_activation=True
        )
        activation = user_with_activation.activation

        assert activation.invite_token_hash is not None
        assert activation.invite_token_expires_at is not None
        assert activation.invite_token_expires_at > datetime.now(UTC)

    async def test_create_pending_email_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_student_request
        )

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
        )
        email = pending_emails[0]

        assert len(pending_emails) == 1
        assert email.recipient == user.email
        assert email.email_type == EmailType.INVITE
        assert email.recipient_user_id == user.id

    async def test_create_user_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_student_request
        )

        assert user.id is not None
        assert user.role == UserRole.STUDENT
        assert user.status == UserStatus.PENDING_ACTIVATION
        assert user.is_active is False
        assert user.password_hash is None
        assert user.date_of_birth == valid_create_student_request.date_of_birth
        assert user.created_by == system_admin.id


class TestRegisterGuardian:
    @pytest.mark.parametrize(
        "existing_factory, duplicate_field, unique_value, expected_exception",
        [
            (
                make_teacher,
                "email",
                "+992555111111",
                MaxStaffOrGuardianPerEmailError,
            ),
            (
                make_teacher,
                "phone_number",
                "different@example.com",
                MaxStaffOrGuardianPerPhoneNumberError,
            ),
            (
                make_guardian,
                "email",
                "+992555222222",
                MaxStaffOrGuardianPerEmailError,
            ),
            (
                make_guardian,
                "phone_number",
                "another@example.com",
                MaxStaffOrGuardianPerPhoneNumberError,
            ),
        ],
    )
    async def test_reject_when_contact_limit_reached(
        self,
        existing_factory,
        duplicate_field,
        unique_value,
        expected_exception,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_guardian_request: CreateGuardianAdmin,
    ):
        email = valid_create_guardian_request.email
        phone = valid_create_guardian_request.phone_number

        if duplicate_field == "email":
            phone = unique_value
        else:
            email = unique_value

        await existing_factory(test_db, email=email, phone_number=phone)

        with pytest.raises(expected_exception):
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_guardian_request
            )

    async def test_create_user_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_guardian_request: CreateGuardianAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_guardian_request
        )

        assert user.id is not None
        assert user.role == UserRole.GUARDIAN
        assert user.status == UserStatus.PENDING_ACTIVATION
        assert user.is_active is False
        assert user.password_hash is None
        assert user.date_of_birth is None
        assert user.address is None
        assert user.created_by == system_admin.id

    async def test_create_pending_email_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_guardian_request: CreateGuardianAdmin,
    ):
        user = await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_guardian_request
        )

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
        )
        email = pending_emails[0]

        assert len(pending_emails) == 1
        assert email.recipient == user.email
        assert email.email_type == EmailType.INVITE
        assert email.recipient_user_id == user.id


class TestAdvisoryLock:
    async def test_advisory_lock_acquired_for_student(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_student_request: CreateStudentAdmin,
        mock_advisory_lock,
    ):
        await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_student_request
        )

        mock_advisory_lock.assert_called_once_with(
            test_db,
            phone_number=valid_create_student_request.phone_number,
            email=valid_create_student_request.email,
        )

    async def test_advisory_lock_not_acquired_for_staff(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_staff_request: CreateStaffAdmin,
        mock_advisory_lock,
    ):
        await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_staff_request
        )

        mock_advisory_lock.assert_not_called()

    async def test_advisory_lock_not_acquired_for_guardian(
        self,
        test_db: AsyncSession,
        system_admin: User,
        valid_create_guardian_request: CreateGuardianAdmin,
        mock_advisory_lock,
    ):
        await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_guardian_request
        )

        mock_advisory_lock.assert_not_called()


class TestUpdateStaffAndGuardian:
    async def test_update_user_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_send_account_info_updated_email,
    ):
        update_request = UpdateStaffAndGuardianAdmin(firstname="UpdatedFirstName")

        updated_user = await UserServiceAdmin.update_user(
            test_db, system_admin.id, teacher.id, update_request
        )

        assert updated_user.firstname == "UpdatedFirstName"

    async def test_update_user_not_found(self, test_db: AsyncSession, system_admin):
        update_request = UpdateStaffAndGuardianAdmin(firstname="DoesntMatter")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, 999_999, update_request
            )

    async def test_update_user_excludes_system_admins(
        self, test_db: AsyncSession, system_admin: User
    ):
        other_admin = await make_system_admin(test_db)
        update_request = UpdateStaffAndGuardianAdmin(firstname="DoesntMatter")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, other_admin.id, update_request
            )

    async def test_update_user_no_fields_set_raises_no_changes(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ):
        update_request = UpdateStaffAndGuardianAdmin()

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, teacher.id, update_request
            )

    async def test_update_user_same_value_raises_no_changes(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ):
        update_request = UpdateStaffAndGuardianAdmin(firstname=teacher.firstname)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, teacher.id, update_request
            )

    async def test_update_non_student_duplicate_phone_raises_error(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        existing = await make_teacher(test_db, phone_number="+992555111333")
        update_request = UpdateStaffAndGuardianAdmin(phone_number=existing.phone_number)

        with pytest.raises(DuplicatePhoneNumberError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, teacher.id, update_request
            )


class TestUpdateStudent:
    async def test_update_student_fields_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
        mock_send_account_info_updated_email,
    ):
        update_request = UpdateStudentAdmin(
            firstname="NewName",
            date_of_birth=date(2007, 6, 15),
            address="123 New Address Street, City",
        )

        updated_user = await UserServiceAdmin.update_user(
            test_db, system_admin.id, student.id, update_request
        )

        assert updated_user.firstname == "NewName"
        assert updated_user.date_of_birth == date(2007, 6, 15)
        assert updated_user.address == "123 New Address Street, City"

    async def test_update_student_phone_acquires_advisory_lock(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
        mock_send_account_info_updated_email,
        mock_acquire_student_contact_lock,
    ):
        update_request = UpdateStudentAdmin(phone_number="+992555999888")

        await UserServiceAdmin.update_user(
            test_db, system_admin.id, student.id, update_request
        )

        mock_acquire_student_contact_lock.assert_called_once_with(
            test_db, phone_number="+992555999888", email=None
        )

    async def test_update_student_phone_unchanged_skips_lock_and_limit(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
        mock_send_account_info_updated_email,
        mock_acquire_student_contact_lock,
        mocker,
    ):
        mock_limit = mocker.patch(
            "src.users.services.system_admin._check_contact_limit",
            return_value=None,
        )

        update_request = UpdateStudentAdmin(phone_number=student.phone_number)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, student.id, update_request
            )

        mock_acquire_student_contact_lock.assert_not_called()
        mock_limit.assert_not_called()

    async def test_update_student_phone_contact_limit_reached(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
    ):
        shared_phone = "+992555111777"

        for i in range(3):
            await make_student(
                test_db,
                phone_number=shared_phone,
                email=f"other_student_{i}@example.com",
                username=f"other_student_{i}",
            )

        update_request = UpdateStudentAdmin(phone_number=shared_phone)

        with pytest.raises(MaxStudentsPerPhoneNumberError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, student.id, update_request
            )

    async def test_update_non_student_phone_skips_advisory_lock(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_send_account_info_updated_email,
        mock_acquire_student_contact_lock,
    ):
        update_request = UpdateStaffAndGuardianAdmin(phone_number="+992555888777")

        await UserServiceAdmin.update_user(
            test_db, system_admin.id, teacher.id, update_request
        )

        mock_acquire_student_contact_lock.assert_not_called()


class TestUpdateUserCredentials:
    async def test_update_username_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_send_admin_credentials_override_notification,
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
        mock_send_admin_credentials_override_notification,
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
        mock_send_admin_credentials_override_notification,
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
        mock_send_admin_credentials_override_notification,
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

    async def test_notification_sent_to_old_email(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_send_admin_credentials_override_notification,
    ):
        old_email = teacher.email
        update_request = UpdateUserCredentials(email="brand.new@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, teacher.id, update_request
        )

        await asyncio.sleep(0)

        mock_send_admin_credentials_override_notification.assert_called_once_with(
            old_email
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
        mock_send_admin_credentials_override_notification,
        mock_acquire_student_contact_lock,
    ):
        update_request = UpdateUserCredentials(email="new.student@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, student.id, update_request
        )

        mock_acquire_student_contact_lock.assert_called_once_with(
            test_db, phone_number=None, email="new.student@example.com"
        )

    async def test_student_email_unchanged_skips_lock_and_limit(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
        mock_acquire_student_contact_lock,
        mock_check_contact_limit,
    ):
        update_request = UpdateUserCredentials(email=student.email)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user_credentials(
                test_db, system_admin.id, student.id, update_request
            )

        mock_acquire_student_contact_lock.assert_not_called()
        mock_check_contact_limit.assert_not_called()

    async def test_non_student_email_change_skips_advisory_lock(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_send_admin_credentials_override_notification,
        mock_acquire_student_contact_lock,
    ):
        update_request = UpdateUserCredentials(email="new.teacher@example.com")

        await UserServiceAdmin.update_user_credentials(
            test_db, system_admin.id, teacher.id, update_request
        )

        mock_acquire_student_contact_lock.assert_not_called()

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


class TestCreateGuardianDeletionRequest:
    async def test_sets_pending_deletion_state_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        guardian: User,
        mock_send_account_deletion_email,
        mock_delete_cache,
    ):
        await UserServiceAdmin.create_guardian_deletion_request(
            test_db, system_admin.id, guardian.id
        )

        updated_user = await UserRepositoryBase.get_user_by_id(test_db, guardian.id)

        assert updated_user.status == UserStatus.PENDING_DELETION
        assert updated_user.is_active is False
        assert updated_user.deletion_scheduled_for is not None

    async def test_resets_session_after_deletion_request(
        self,
        test_db: AsyncSession,
        system_admin: User,
        guardian: User,
        mock_send_account_deletion_email,
        mock_delete_cache,
    ):
        await UserServiceAdmin.create_guardian_deletion_request(
            test_db, system_admin.id, guardian.id
        )

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, guardian.id, load_session=True
        )
        session = user_with_session.session

        assert session.access_token_version == 2
        assert session.refresh_token_hash is None
        assert session.refresh_token_family is None
        assert session.refresh_token_expires_at is None

    async def test_cache_invalidated_including_token_version(
        self,
        test_db: AsyncSession,
        system_admin: User,
        guardian: User,
        mock_send_account_deletion_email,
        mock_delete_cache,
    ):
        await UserServiceAdmin.create_guardian_deletion_request(
            test_db, system_admin.id, guardian.id
        )

        mock_delete_cache.assert_called_once_with(
            SessionCacheKey.access_token_version_key(guardian.id),
            UserCacheKey.user_detail_key_admin(guardian.id),
        )

    async def test_not_found_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_guardian_deletion_request(
                test_db, system_admin.id, 999_999
            )

    async def test_non_guardian_role_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_guardian_deletion_request(
                test_db, system_admin.id, teacher.id
            )

    async def test_already_pending_deletion_raises_error(
        self,
        test_db: AsyncSession,
        system_admin: User,
        mock_send_account_deletion_email,
        mock_delete_cache,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )

        with pytest.raises(UserAlreadyPendingDeletionError):
            await UserServiceAdmin.create_guardian_deletion_request(
                test_db, system_admin.id, guardian_pending.id
            )


class TestCancelGuardianDeletionRequest:
    async def test_cancels_deletion_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        mock_send_account_deletion_canceled_email,
        mock_delete_cache,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )

        await UserServiceAdmin.cancel_guardian_deletion_request(
            test_db, system_admin.id, guardian_pending.id
        )

        updated_user = await UserRepositoryBase.get_user_by_id(
            test_db, guardian_pending.id
        )

        assert updated_user.status != UserStatus.PENDING_DELETION

    async def test_cache_invalidated_after_cancellation(
        self,
        test_db: AsyncSession,
        system_admin: User,
        mock_send_account_deletion_canceled_email,
        mock_delete_cache,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )

        await UserServiceAdmin.cancel_guardian_deletion_request(
            test_db, system_admin.id, guardian_pending.id
        )

        mock_delete_cache.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(guardian_pending.id),
        )

    async def test_not_found_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.cancel_guardian_deletion_request(
                test_db, system_admin.id, 999_999
            )

    async def test_non_pending_guardian_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
        guardian: User,
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.cancel_guardian_deletion_request(
                test_db, system_admin.id, guardian.id
            )

    async def test_lost_race_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
        mocker,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )

        mocker.patch(
            "src.users.services.system_admin.UserRepositoryBase.reactivate_pending_deletion_user",
            return_value=False,
        )

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.cancel_guardian_deletion_request(
                test_db, system_admin.id, guardian_pending.id
            )


class TestDeactivateUser:
    async def test_deactivate_user_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_delete_cache,
    ):
        await UserServiceAdmin.deactivate_user(test_db, system_admin.id, teacher.id)

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )

        assert user_with_session.is_active is False
        assert user_with_session.session.access_token_version == 2
        assert user_with_session.session.refresh_token_hash is None
        assert user_with_session.session.refresh_token_family is None
        assert user_with_session.session.refresh_token_expires_at is None

    async def test_deactivate_user_invalidates_cache(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_delete_cache,
    ):
        await UserServiceAdmin.deactivate_user(test_db, system_admin.id, teacher.id)

        mock_delete_cache.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(teacher.id),
            UserCacheKey.user_detail_key_staff(teacher.id),
            UserCacheKey.user_detail_key_self(teacher.id),
            SessionCacheKey.access_token_version_key(teacher.id),
        )

    async def test_deactivate_user_not_found(
        self, test_db: AsyncSession, system_admin: User
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.deactivate_user(test_db, system_admin.id, 999_999)

    async def test_deactivate_already_inactive_user(
        self, test_db: AsyncSession, system_admin: User
    ):
        deactivated = await make_deactivated_user(test_db)

        with pytest.raises(UserAlreadyInactiveError):
            await UserServiceAdmin.deactivate_user(
                test_db, system_admin.id, deactivated.id
            )

    async def test_deactivate_user_excludes_system_admins(
        self, test_db: AsyncSession, system_admin: User
    ):
        other_admin = await make_system_admin(test_db)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.deactivate_user(
                test_db, system_admin.id, other_admin.id
            )


class TestActivateUser:
    async def test_activate_user_successfully(
        self, test_db: AsyncSession, system_admin: User, mock_delete_cache
    ):
        deactivated = await make_deactivated_user(test_db)

        await UserServiceAdmin.activate_user(test_db, system_admin.id, deactivated.id)

        activated_user = await UserRepositoryBase.get_user_by_id(
            test_db, deactivated.id
        )
        assert activated_user.is_active is True

    async def test_activate_user_invalidates_cache(
        self, test_db: AsyncSession, system_admin: User, mock_delete_cache
    ):
        deactivated = await make_deactivated_user(test_db)

        await UserServiceAdmin.activate_user(test_db, system_admin.id, deactivated.id)

        mock_delete_cache.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(deactivated.id)
        )

    async def test_activate_user_not_found(
        self, test_db: AsyncSession, system_admin: User
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.activate_user(test_db, system_admin.id, 999_999)

    async def test_activate_already_active_user(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ):
        with pytest.raises(UserAlreadyActiveError):
            await UserServiceAdmin.activate_user(test_db, system_admin.id, teacher.id)

    async def test_activate_user_excludes_system_admins(
        self, test_db: AsyncSession, system_admin: User
    ):
        other_admin = await make_deactivated_user(test_db, role=UserRole.SYSTEM_ADMIN)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.activate_user(
                test_db, system_admin.id, other_admin.id
            )


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
        self, test_db, system_admin
    ):
        target = await make_user(
            test_db, role=UserRole.TEACHER, status=UserStatus.PENDING_ACTIVATION,
        )
        target = await UserRepositoryBase.get_user_by_id(test_db, target.id, load_activation=True)
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

    async def test_new_expiry_is_settings_window_from_now(self, test_db, system_admin):
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

    async def test_target_user_not_found_raises(self, test_db, system_admin):
        nonexistent_id = 999_999_999

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.resend_activation_invite(
                test_db, system_admin.id, nonexistent_id
            )

    async def test_target_role_excluded_from_system_admin_raises_not_found(
        self, test_db, system_admin
    ):
        other_admin = await make_system_admin(
            test_db, status=UserStatus.PENDING_ACTIVATION
        )

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.resend_activation_invite(
                test_db, system_admin.id, other_admin.id
            )

    async def test_target_not_pending_activation_raises(self, test_db, system_admin):
        active_target = await make_teacher(test_db, status=UserStatus.ACTIVE)

        with pytest.raises(UserNotPendingActivationError):
            await UserServiceAdmin.resend_activation_invite(
                test_db, system_admin.id, active_target.id
            )

    async def test_deactivated_target_raises_not_pending(self, test_db, system_admin):
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

