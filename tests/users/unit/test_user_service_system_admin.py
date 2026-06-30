from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import CurrentUser
from emails.repository import PendingEmailRepository
from src.emails.models import EmailType
from src.utils.exceptions import (
    CannotCreateDirectorError,
    CannotCreateStudentError,
    CannotCreateSystemAdminError,
    DuplicateValueError,
    MaxNumberOfIdenticalContactsError,
    NoChangesDetectedError,
    UserAlreadyActiveError,
    UserAlreadyInactiveError,
    UsernameAlreadyTakenError,
    UserNotFoundError,
)
from tests.factories import (
    make_deactivated_user,
    make_student,
    make_system_admin,
    make_teacher,
)
from users.models.users import User
from users.repositories.users_admin import UserRepositoryBase
from users.schemas.users import (
    CreateStaffAdmin,
    CreateStudentAdmin,
    UpdateUser,
    UpdateUserEmail,
)
from users.services.user_management import UserServiceAdmin
from utils.cache_keys import SessionCacheKey, UserCacheKey
from utils.enums import UserRole, UserStatus


class TestRegisterStaff:
    async def test_block_system_admin_creation(
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
    ):
        valid_create_staff_request.role = UserRole.SYSTEM_ADMIN

        with pytest.raises(CannotCreateSystemAdminError):
            await UserServiceAdmin.register_staff(
                test_db, system_admin.id, valid_create_staff_request
            )

    async def test_block_director_creation(
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
    ):
        valid_create_staff_request.role = UserRole.DIRECTOR

        with pytest.raises(CannotCreateDirectorError):
            await UserServiceAdmin.register_staff(
                test_db, system_admin.id, valid_create_staff_request
            )

    async def test_block_student_creation(
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
    ):
        valid_create_staff_request.role = UserRole.STUDENT

        with pytest.raises(CannotCreateStudentError):
            await UserServiceAdmin.register_staff(
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
                {"email": "taken@example.com", "phone_number": "+15551112222"},
                {"email": "taken@example.com", "phone_number": "+15551112222"},
                MaxNumberOfIdenticalContactsError,
            ),
        ],
    )
    async def test_reject_duplicate_fields(
        self,
        test_db,
        system_admin,
        valid_create_staff_request: CreateStaffAdmin,
        existing_user_data: dict,
        request_override: dict,
        expected_exception,
    ):
        await make_teacher(test_db, **existing_user_data)

        for field, value in request_override.items():
            setattr(valid_create_staff_request, field, value)

        with pytest.raises(expected_exception):
            await UserServiceAdmin.register_staff(
                test_db, system_admin.id, valid_create_staff_request
            )

    async def test_create_user_session_table_successfully(
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
    ):
        user = await UserServiceAdmin.register_staff(
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
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
    ):
        user = await UserServiceAdmin.register_staff(
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
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
    ):
        user = await UserServiceAdmin.register_staff(
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
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
    ):
        user = await UserServiceAdmin.register_staff(
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
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
    ):
        user = await UserServiceAdmin.register_staff(
            test_db, system_admin.id, valid_create_staff_request
        )

        assert user.id is not None
        assert user.email == valid_create_staff_request.email
        assert user.role == valid_create_staff_request.role
        assert user.status == UserStatus.PENDING_ACTIVATION
        assert user.is_active is False
        assert user.password_hash is None
        assert user.created_by == system_admin.id

    @pytest.mark.db_constraint
    async def test_contact_limit_db_constraint_catches_bypassed_precheck(
        self,
        test_db,
        system_admin,
        valid_create_staff_request: CreateStaffAdmin,
        mocker,
    ):
        """Proves uix_non_student_unique_contact is the real backstop,
        independent of _check_contact_limit's pre-check."""
        await make_teacher(
            test_db, email="constraint.check@example.com", phone_number="+15551112233"
        )

        mocker.patch(
            "src.users.service.UserRepositoryBase.count_users_with_contact",
            return_value=0,
        )

        valid_create_staff_request.email = "constraint.check@example.com"
        valid_create_staff_request.phone_number = "+15551112233"

        with pytest.raises(DuplicateValueError):
            await UserServiceAdmin.register_staff(
                test_db, system_admin.id, valid_create_staff_request
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
        test_db,
        system_admin,
        valid_create_student_request: CreateStudentAdmin,
        existing_user_data: dict,
        request_override: dict,
        expected_exception,
    ):
        await make_teacher(test_db, **existing_user_data)

        for field, value in request_override.items():
            setattr(valid_create_student_request, field, value)

        with pytest.raises(expected_exception):
            await UserServiceAdmin.register_student(
                test_db, system_admin.id, valid_create_student_request
            )

    async def test_reject_when_contact_limit_reached(
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
    ):
        for i in range(3):
            await make_student(
                test_db,
                email="shared@example.com",
                phone_number="+15553334444",
                username=f"existing_student_{i}",
            )

        valid_create_student_request.email = "shared@example.com"
        valid_create_student_request.phone_number = "+15553334444"

        with pytest.raises(MaxNumberOfIdenticalContactsError):
            await UserServiceAdmin.register_student(
                test_db, system_admin.id, valid_create_student_request
            )

    async def test_create_user_session_table_successfully(
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
    ):
        user = await UserServiceAdmin.register_student(
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
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
    ):
        user = await UserServiceAdmin.register_student(
            test_db, system_admin.id, valid_create_student_request
        )

        user_with_lockout = await UserRepositoryBase.get_user_by_id(
            test_db, user.id, load_login_lockout=True
        )
        lockout = user_with_lockout.login_lockout

        assert lockout.failed_login_attempts == 0
        assert lockout.locked_until is None

    async def test_create_user_activation_table_successfully(
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
    ):
        user = await UserServiceAdmin.register_student(
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
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
    ):
        user = await UserServiceAdmin.register_student(
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
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
    ):
        user = await UserServiceAdmin.register_student(
            test_db, system_admin.id, valid_create_student_request
        )

        assert user.id is not None
        assert user.role == UserRole.STUDENT
        assert user.status == UserStatus.PENDING_ACTIVATION
        assert user.is_active is False
        assert user.password_hash is None
        assert user.date_of_birth == valid_create_student_request.date_of_birth
        assert user.created_by == system_admin.id


class TestDeleteParent:
    async def test_delete_parent_successfully(
        self, test_db: AsyncSession, system_admin: User, parent: User
    ) -> None:
        await UserServiceAdmin.delete_parent(test_db, system_admin.id, parent.id)

        deleted_user = await UserRepositoryBase.get_user_by_id(test_db, parent.id)
        assert deleted_user is None

    async def test_delete_parent_not_found(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.delete_parent(test_db, system_admin.id, 999_999)

    async def test_delete_parent_rejects_non_parent_role(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ) -> None:
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.delete_parent(test_db, system_admin.id, teacher.id)


class TestDeactivateUser:
    async def test_deactivate_user_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_delete_cache: AsyncMock,
    ) -> None:
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
        mock_delete_cache: AsyncMock,
    ) -> None:
        await UserServiceAdmin.deactivate_user(test_db, system_admin.id, teacher.id)

        mock_delete_cache.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(teacher.id),
            SessionCacheKey.access_token_version_key(teacher.id),
        )

    async def test_deactivate_user_not_found(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.deactivate_user(test_db, system_admin.id, 999_999)

    async def test_deactivate_already_inactive_user(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        deactivated = await make_deactivated_user(test_db)

        with pytest.raises(UserAlreadyInactiveError):
            await UserServiceAdmin.deactivate_user(
                test_db, system_admin.id, deactivated.id
            )

    async def test_deactivate_user_excludes_system_admins(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        other_admin = await make_system_admin(test_db)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.deactivate_user(
                test_db, system_admin.id, other_admin.id
            )


class TestActivateUser:
    async def test_activate_user_successfully(
        self, test_db: AsyncSession, system_admin: User, mock_delete_cache: AsyncMock
    ) -> None:
        deactivated = await make_deactivated_user(test_db)

        await UserServiceAdmin.activate_user(test_db, system_admin.id, deactivated.id)

        activated_user = await UserRepositoryBase.get_user_by_id(
            test_db, deactivated.id
        )
        assert activated_user.is_active is True

    async def test_activate_user_invalidates_cache(
        self, test_db: AsyncSession, system_admin: User, mock_delete_cache: AsyncMock
    ) -> None:
        deactivated = await make_deactivated_user(test_db)

        await UserServiceAdmin.activate_user(test_db, system_admin.id, deactivated.id)

        mock_delete_cache.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(deactivated.id)
        )

    async def test_activate_user_not_found(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.activate_user(test_db, system_admin.id, 999_999)

    async def test_activate_already_active_user(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ) -> None:
        with pytest.raises(UserAlreadyActiveError):
            await UserServiceAdmin.activate_user(test_db, system_admin.id, teacher.id)

    async def test_activate_user_excludes_system_admins(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        other_admin = await make_deactivated_user(test_db, role=UserRole.SYSTEM_ADMIN)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.activate_user(
                test_db, system_admin.id, other_admin.id
            )


class TestUpdateUser:
    async def test_update_user_successfully(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ) -> None:
        update_request = UpdateUser(firstname="UpdatedFirstName")

        updated_user = await UserServiceAdmin.update_user(
            test_db, system_admin.id, teacher.id, update_request
        )

        assert updated_user.firstname == "UpdatedFirstName"

    async def test_update_user_not_found(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        update_request = UpdateUser(firstname="DoesntMatter")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, 999_999, update_request
            )

    async def test_update_user_excludes_system_admins(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        other_admin = await make_system_admin(test_db)
        update_request = UpdateUser(firstname="DoesntMatter")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, other_admin.id, update_request
            )

    async def test_update_user_no_fields_set_raises_no_changes(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ) -> None:
        update_request = UpdateUser()

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, teacher.id, update_request
            )

    async def test_update_user_same_value_raises_no_changes(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ) -> None:
        update_request = UpdateUser(firstname=teacher.firstname)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, teacher.id, update_request
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
                {"email": "taken@example.com", "phone_number": "+15551239876"},
                {"phone_number": "+15551239876"},
                DuplicateValueError,
            ),
        ],
    )
    async def test_update_user_rejects_duplicate_fields(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        existing_user_data: dict,
        request_override: dict,
        expected_exception,
    ) -> None:
        await make_teacher(test_db, **existing_user_data)
        update_request = UpdateUser(**request_override)

        with pytest.raises(expected_exception):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, teacher.id, update_request
            )


class TestUpdateUserEmail:
    async def test_update_user_email_successfully(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ) -> None:
        update_request = UpdateUserEmail(new_email="new.email@example.com")

        await UserServiceAdmin.update_user_email(
            test_db, system_admin.id, teacher.id, update_request
        )

        updated_user = await UserRepositoryBase.get_user_by_id(test_db, teacher.id)
        assert updated_user.email == "new.email@example.com"

    async def test_update_user_email_resets_session_fields(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ) -> None:
        update_request = UpdateUserEmail(new_email="new.email2@example.com")

        await UserServiceAdmin.update_user_email(
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

    async def test_update_user_email_not_found(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        update_request = UpdateUserEmail(new_email="nobody@example.com")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user_email(
                test_db, system_admin.id, 999_999, update_request
            )

    async def test_update_user_email_excludes_system_admins(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        other_admin = await make_system_admin(test_db)
        update_request = UpdateUserEmail(new_email="nobody2@example.com")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user_email(
                test_db, system_admin.id, other_admin.id, update_request
            )

    async def test_update_user_email_rejects_duplicate_contact(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ) -> None:
        await make_teacher(
            test_db, email="taken@example.com", phone_number=teacher.phone_number
        )
        update_request = UpdateUserEmail(new_email="taken@example.com")

        with pytest.raises(DuplicateValueError):
            await UserServiceAdmin.update_user_email(
                test_db, system_admin.id, teacher.id, update_request
            )


class TestCreateResetPasswordRequest:
    async def test_creates_reset_password_request_successfully(
        self, test_db: AsyncSession, system_admin: User, teacher: User
    ) -> None:
        current_user = CurrentUser(system_admin.id, system_admin.role)

        await UserServiceAdmin.create_reset_password_request(
            test_db, current_user, teacher.id
        )

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )
        session = user_with_session.session

        assert session.reset_password_token_hash is not None
        assert session.reset_password_token_expires_at is not None

        pending_emails = await PendingEmailRepository.get_pending_email_by_triggered_by(
            test_db, system_admin.id
        )
        assert len(pending_emails) == 1
        assert pending_emails[0].recipient_user_id == teacher.id

    async def test_create_reset_password_request_not_found(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        current_user = CurrentUser(system_admin.id, system_admin.role)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_reset_password_request(
                test_db, current_user, 999_999
            )

    async def test_create_reset_password_request_excludes_system_admins(
        self, test_db: AsyncSession, system_admin: User
    ) -> None:
        other_admin = await make_system_admin(test_db)
        current_user = CurrentUser(system_admin.id, system_admin.role)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_reset_password_request(
                test_db, current_user, other_admin.id
            )
