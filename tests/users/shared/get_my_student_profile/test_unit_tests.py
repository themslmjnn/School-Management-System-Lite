import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import CurrentUser
from src.users.services.shared import UserServiceSelf
from src.utils.enums import UserRole
from tests.factories import make_group, make_student, make_teacher


class TestGetMyStudentProfile:
    async def test_returns_profile_for_student(self, session: AsyncSession):
        group = await make_group(session, name="Test Group A")
        user = await make_student(
            session, username="profile_student", group_id=group.id
        )
        current_user = CurrentUser(id=user.id, role=user.role)

        result = await UserServiceSelf.get_my_student_profile(session, current_user)

        assert result.id == user.id
        assert result.username == user.username

    async def test_student_profile_includes_group(self, session: AsyncSession):
        group = await make_group(session, name="Group With Student")
        user = await make_student(session, username="student_group", group_id=group.id)
        current_user = CurrentUser(id=user.id, role=user.role)

        result = await UserServiceSelf.get_my_student_profile(session, current_user)

        assert result.group is not None

    async def test_student_profile_without_group(self, session: AsyncSession):
        user = await make_student(session, username="student_no_group")
        current_user = CurrentUser(id=user.id, role=user.role)

        result = await UserServiceSelf.get_my_student_profile(session, current_user)

        assert result.group is None

    async def test_non_student_role_returns_404(self, session: AsyncSession):
        from src.users.utils.exceptions import UserNotFoundError

        user = await make_teacher(session, username="teacher_as_student")
        current_user = CurrentUser(id=user.id, role=UserRole.STUDENT)

        with pytest.raises(UserNotFoundError):
            await UserServiceSelf.get_my_student_profile(session, current_user)

    async def test_caches_student_profile_on_first_call(
        self, session: AsyncSession, mock_set_cache_user_shared
    ):
        user = await make_student(session, username="student_cache")
        current_user = CurrentUser(id=user.id, role=user.role)

        await UserServiceSelf.get_my_student_profile(session, current_user)

        mock_set_cache_user_shared.assert_awaited_once()
