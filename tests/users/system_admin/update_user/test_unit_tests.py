from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.users.services.system_admin import UserServiceAdmin
from src.users.utils.exceptions import (
    DuplicatePhoneNumberError,
    MaxStudentsPerPhoneNumberError,
    UserNotFoundError,
    UserTypeMismatchError,
)
from src.utils.base_exception import NoChangesDetectedError
from tests.factories import (
    make_student,
    make_system_admin,
    make_teacher,
)
from src.users.schemas.system_admin import (
    UpdateStudentAdmin,
    UpdateTeacherAdmin,
)
from src.users.repositories.user import UserRepositoryBase


class TestUpdateTeacher:
    async def test_update_user_successfully(
        self,
        session: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_send_account_info_updated_email,
    ):
        update_request = UpdateTeacherAdmin(firstname="UpdatedFirstName")
        target_teacher_id = teacher.id

        await UserServiceAdmin.update_user(
            session, system_admin.id, target_teacher_id, update_request
        )

        updated_user = await UserRepositoryBase.get_user_by_id(
            session, target_teacher_id
        )

        assert updated_user.firstname == "Updatedfirstname"

    async def test_update_user_not_found(
        self, session: AsyncSession, system_admin: User
    ):
        update_request = UpdateTeacherAdmin(firstname="DoesntMatter")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user(
                session, system_admin.id, 999_999, update_request
            )

    async def test_update_user_excludes_system_admins(
        self, session: AsyncSession, system_admin: User
    ):
        other_admin = await make_system_admin(session)
        update_request = UpdateTeacherAdmin(firstname="DoesntMatter")

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.update_user(
                session, system_admin.id, other_admin.id, update_request
            )

    async def test_update_user_no_fields_set_raises_no_changes(
        self, session: AsyncSession, system_admin: User, teacher: User
    ):
        update_request = UpdateTeacherAdmin()

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user(
                session, system_admin.id, teacher.id, update_request
            )

    async def test_update_user_same_value_raises_no_changes(
        self, session: AsyncSession, system_admin: User, teacher: User
    ):
        update_request = UpdateTeacherAdmin(firstname=teacher.firstname)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user(
                session, system_admin.id, teacher.id, update_request
            )

    async def test_update_non_student_duplicate_phone_raises_error(
        self,
        session: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        existing = await make_teacher(session, phone_number="+992555111333")
        update_request = UpdateTeacherAdmin(phone_number=existing.phone_number)

        with pytest.raises(DuplicatePhoneNumberError):
            await UserServiceAdmin.update_user(
                session, system_admin.id, teacher.id, update_request
            )

    async def test_student_payload_sent_to_teacher_target_raises_type_mismatch(
        self,
        session: AsyncSession,
        system_admin: User,
        teacher: User,
    ) -> None:
        update_request = UpdateStudentAdmin(firstname="NewName")

        with pytest.raises(UserTypeMismatchError):
            await UserServiceAdmin.update_user(
                session, system_admin.id, teacher.id, update_request
            )


class TestUpdateStudent:
    async def test_update_student_fields_successfully(
        self,
        session: AsyncSession,
        system_admin: User,
        student: User,
        mock_send_account_info_updated_email,
    ):
        update_request = UpdateStudentAdmin(
            firstname="NewName",
            date_of_birth=date(2007, 6, 15),
            address="123 New Address Street, City",
        )
        target_student_id = student.id

        await UserServiceAdmin.update_user(
            session, system_admin.id, target_student_id, update_request
        )

        updated_user = await UserRepositoryBase.get_user_by_id(
            session, target_student_id
        )

        assert updated_user.firstname == "Newname"
        assert updated_user.date_of_birth == date(2007, 6, 15)
        assert updated_user.address == "123 New Address Street, City"

    async def test_update_student_phone_acquires_advisory_lock(
        self,
        session: AsyncSession,
        system_admin: User,
        student: User,
        mock_send_account_info_updated_email,
        mock_advisory_lock,
    ):
        update_request = UpdateStudentAdmin(phone_number="+992555999888")

        await UserServiceAdmin.update_user(
            session, system_admin.id, student.id, update_request
        )

        mock_advisory_lock.assert_called_once_with(
            session, phone_number="+992555999888", email=None
        )

    async def test_update_student_phone_unchanged_skips_lock_and_limit(
        self,
        session: AsyncSession,
        system_admin: User,
        student: User,
        mock_send_account_info_updated_email,
        mock_advisory_lock,
        mock_check_contact_limit,
    ):
        update_request = UpdateStudentAdmin(phone_number=student.phone_number)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceAdmin.update_user(
                session, system_admin.id, student.id, update_request
            )

        mock_advisory_lock.assert_not_called()
        mock_check_contact_limit.assert_not_called()

    async def test_update_student_phone_contact_limit_reached(
        self,
        session: AsyncSession,
        system_admin: User,
        student: User,
    ):
        shared_phone = "+992555111777"

        for i in range(3):
            await make_student(
                session,
                phone_number=shared_phone,
                email=f"other_student_{i}@example.com",
                username=f"other_student_{i}",
            )

        update_request = UpdateStudentAdmin(phone_number=shared_phone)

        with pytest.raises(MaxStudentsPerPhoneNumberError):
            await UserServiceAdmin.update_user(
                session, system_admin.id, student.id, update_request
            )

    async def test_update_non_student_phone_skips_advisory_lock(
        self,
        session: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_send_account_info_updated_email,
        mock_advisory_lock,
    ):
        update_request = UpdateTeacherAdmin(phone_number="+992555888777")

        await UserServiceAdmin.update_user(
            session, system_admin.id, teacher.id, update_request
        )

        mock_advisory_lock.assert_not_called()

    async def test_teacher_payload_sent_to_student_target_raises_type_mismatch(
        self,
        session: AsyncSession,
        system_admin: User,
        student: User,
    ) -> None:
        update_request = UpdateTeacherAdmin(firstname="NewName")

        with pytest.raises(UserTypeMismatchError):
            await UserServiceAdmin.update_user(
                session, system_admin.id, student.id, update_request
            )
