from datetime import UTC, datetime

import pytest

from src.emails.models import EmailType
from src.emails.repository import PendingEmailRepository
from src.users.repositories.users import UserRepositoryBase
from src.users.schemas.users import (
    CreateGuardianAdmin,
    CreateStaffAdmin,
    CreateStudentAdmin,
)
from src.users.services.system_admin import UserServiceAdmin
from src.utils.enums import UserRole, UserStatus
from src.utils.exceptions import (
    CannotCreateDirectorError,
    CannotCreateSystemAdminError,
    DuplicateValueError,
    MaxNumberOfIdenticalContactsError,
    MaxStaffOrGuardianPerEmailError,
    MaxStaffOrGuardianPerPhoneNumberError,
    MaxStudentsPerEmailError,
    MaxStudentsPerPhoneNumberError,
    UsernameAlreadyTakenError,
)
from tests.factories import make_guardian, make_student, make_teacher


class TestRegisterStaff:
    async def test_block_system_admin_creation(
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
    ):
        valid_create_staff_request.role = UserRole.SYSTEM_ADMIN

        with pytest.raises(CannotCreateSystemAdminError):
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_staff_request
            )

    async def test_block_director_creation(
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
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
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_staff_request
            )

    async def test_create_user_session_table_successfully(
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
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
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
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
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
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
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
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
        self, test_db, system_admin, valid_create_staff_request: CreateStaffAdmin
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
    async def test_contact_limit_db_constraint_catches_bypassed_precheck(
        self,
        test_db,
        system_admin,
        valid_create_staff_request: CreateStaffAdmin,
        mocker,
    ):
        await make_teacher(
            test_db, email="constraint.check@example.com", phone_number="+992555111333"
        )

        mocker.patch(
            "src.users.services.system_admin.UserRepositoryBase.count_users_with_contact",
            return_value=0,
        )

        valid_create_staff_request.email = "constraint.check@example.com"
        valid_create_staff_request.phone_number = "+992555111333"

        with pytest.raises(DuplicateValueError):
            await UserServiceAdmin.register_user(
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
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_student_request
            )

    @pytest.mark.parametrize(
        ("field", "value", "expected_exception"),
        [
            ("email", "shared@example.com", MaxStudentsPerEmailError),
            (
                "phone_number",
                "+992555333444",
                MaxStudentsPerPhoneNumberError,
            ),
        ],
    )
    async def test_reject_when_student_contact_limit_reached(
        self,
        test_db,
        system_admin,
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
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
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
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
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
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
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
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
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
        self, test_db, system_admin, valid_create_student_request: CreateStudentAdmin
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
    async def test_reject_when_contact_limit_reached(
        self, test_db, system_admin, valid_create_guardian_request: CreateGuardianAdmin
    ):
        await make_teacher(
            test_db,
            email=valid_create_guardian_request.email,
            phone_number=valid_create_guardian_request.phone_number,
        )

        with pytest.raises(MaxNumberOfIdenticalContactsError):
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_guardian_request
            )

    async def test_staff_and_guardian_share_contact_pool(
        self, test_db, system_admin, valid_create_guardian_request: CreateGuardianAdmin
    ):
        await make_guardian(
            test_db,
            email=valid_create_guardian_request.email,
            phone_number=valid_create_guardian_request.phone_number,
        )

        with pytest.raises(MaxNumberOfIdenticalContactsError):
            await UserServiceAdmin.register_user(
                test_db, system_admin.id, valid_create_guardian_request
            )

    async def test_create_user_successfully(
        self, test_db, system_admin, valid_create_guardian_request: CreateGuardianAdmin
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
        self, test_db, system_admin, valid_create_guardian_request: CreateGuardianAdmin
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
        test_db,
        system_admin,
        valid_create_student_request: CreateStudentAdmin,
        mocker,
    ):
        mock_lock = mocker.patch(
            "src.users.services.system_admin.acquire_student_contact_lock",
            return_value=None,
        )

        await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_student_request
        )

        mock_lock.assert_called_once_with(
            test_db,
            phone_number=valid_create_student_request.phone_number,
            email=valid_create_student_request.email,
        )

    async def test_advisory_lock_not_acquired_for_staff(
        self,
        test_db,
        system_admin,
        valid_create_staff_request: CreateStaffAdmin,
        mocker,
    ):
        mock_lock = mocker.patch(
            "src.users.services.system_admin.acquire_student_contact_lock",
            return_value=None,
        )

        await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_staff_request
        )

        mock_lock.assert_not_called()

    async def test_advisory_lock_not_acquired_for_guardian(
        self,
        test_db,
        system_admin,
        valid_create_guardian_request: CreateGuardianAdmin,
        mocker,
    ):
        mock_lock = mocker.patch(
            "src.users.services.system_admin.acquire_student_contact_lock",
            return_value=None,
        )

        await UserServiceAdmin.register_user(
            test_db, system_admin.id, valid_create_guardian_request
        )

        mock_lock.assert_not_called()
