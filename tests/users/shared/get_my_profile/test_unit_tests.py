import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import CurrentUser
from src.users.services.shared import UserServiceSelf
from src.users.utils.exceptions import UserNotFoundError
from src.utils.enums import UserRole
from tests.factories import make_director, make_student, make_teacher


class TestGetMyProfile:
    async def test_returns_profile_for_non_student(self, session: AsyncSession):
        user = await make_teacher(session, username="teacher")
        current_user = CurrentUser(id=user.id, role=user.role)

        result = await UserServiceSelf.get_my_profile(session, current_user)

        assert result.id == user.id
        assert result.username == user.username

    async def test_returns_profile_for_director(self, session: AsyncSession):
        user = await make_director(session, username="director")
        current_user = CurrentUser(id=user.id, role=user.role)

        result = await UserServiceSelf.get_my_profile(session, current_user)

        assert result.id == user.id

    async def test_caches_profile_on_first_call(
        self, session: AsyncSession, mock_set_cache_user_shared
    ):
        user = await make_teacher(session, username="cache_teacher")
        current_user = CurrentUser(id=user.id, role=user.role)

        await UserServiceSelf.get_my_profile(session, current_user)

        mock_set_cache_user_shared.assert_awaited_once()

    async def test_phone_number_excluded_format_phone_present(
        self, session: AsyncSession
    ):
        user = await make_teacher(session, username="phone_teacher")
        current_user = CurrentUser(id=user.id, role=user.role)

        result = await UserServiceSelf.get_my_profile(session, current_user)
        serialized = result.model_dump()

        assert "phone_number" not in serialized
        assert "format_phone_number" in serialized

    async def test_student_excluded_from_get_my_profile(self, session: AsyncSession):
        user = await make_student(session, username="student_excluded")
        current_user = CurrentUser(id=user.id, role=UserRole.STUDENT)

        with pytest.raises(UserNotFoundError):
            await UserServiceSelf.get_my_profile(session, current_user)
