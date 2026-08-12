from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from users.utils.exceptions import (
    DuplicatePhoneNumberError,
    MaxStudentsPerPhoneNumberError,
    UserNotFoundError,
    UserTypeMismatchError,
)
from src.users.models.user import User
from users.schemas.system_admin import (
    UpdateStaffAndGuardianAdmin,
    UpdateStudentAdmin,
)
from users.services.system_admin import UserServiceAdmin
from src.utils.base_exception import NoChangesDetectedError
from tests.factories import (
    make_student,
    make_system_admin,
    make_teacher,
)


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

        assert updated_user.firstname == "Updatedfirstname"

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

    async def test_student_payload_sent_to_staff_target_raises_type_mismatch(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ) -> None:
        update_request = UpdateStudentAdmin(firstname="NewName")

        with pytest.raises(UserTypeMismatchError):
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

        assert updated_user.firstname == "Newname"
        assert updated_user.date_of_birth == date(2007, 6, 15)
        assert updated_user.address == "123 New Address Street, City"

    async def test_update_student_phone_acquires_advisory_lock(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
        mock_send_account_info_updated_email,
        mock_advisory_lock,
    ):
        update_request = UpdateStudentAdmin(phone_number="+992555999888")

        await UserServiceAdmin.update_user(
            test_db, system_admin.id, student.id, update_request
        )

        mock_advisory_lock.assert_called_once_with(
            test_db, phone_number="+992555999888", email=None
        )

    async def test_update_student_phone_unchanged_skips_lock_and_limit(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
        mock_send_account_info_updated_email,
        mock_advisory_lock,
        mock_check_contact_limit,
    ):
        update_request = UpdateStudentAdmin(phone_number=student.phone_number)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, student.id, update_request
            )

        mock_advisory_lock.assert_not_called()
        mock_check_contact_limit.assert_not_called()

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
        mock_advisory_lock,
    ):
        update_request = UpdateStaffAndGuardianAdmin(phone_number="+992555888777")

        await UserServiceAdmin.update_user(
            test_db, system_admin.id, teacher.id, update_request
        )

        mock_advisory_lock.assert_not_called()

    async def test_staff_payload_sent_to_student_target_raises_type_mismatch(
        self,
        test_db: AsyncSession,
        system_admin: User,
        student: User,
    ) -> None:
        update_request = UpdateStaffAndGuardianAdmin(firstname="NewName")

        with pytest.raises(UserTypeMismatchError):
            await UserServiceAdmin.update_user(
                test_db, system_admin.id, student.id, update_request
            )
