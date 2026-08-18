import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.users.services.system_admin import UserServiceAdmin
from src.users.utils.exceptions import UserNotFoundError
from src.utils.cache_keys import UserCacheKey
from src.utils.enums import UserRole
from tests.factories import (
    make_director,
    make_student,
    make_system_admin,
)


class TestGetTeacherById:
    async def test_returns_correct_data(self, session: AsyncSession, teacher: User):
        result = await UserServiceAdmin.get_teacher_by_id(session, teacher.id)

        assert result.id == teacher.id
        assert result.email == teacher.email
        assert result.role == UserRole.TEACHER

    async def test_returns_404_when_not_found(self, session):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.get_teacher_by_id(session, 999_999)

    @pytest.mark.parametrize(
        "factory",
        [make_student, make_director, make_system_admin],
    )
    async def test_returns_404_for_non_staff_role(self, session: AsyncSession, factory):
        non_staff = await factory(session)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.get_teacher_by_id(session, non_staff.id)

    async def test_populates_cache_after_db_hit(
        self,
        session: AsyncSession,
        teacher: User,
        mock_set_cache_user_system_admin,
        mocker,
    ):
        await UserServiceAdmin.get_teacher_by_id(session, teacher.id)

        mock_set_cache_user_system_admin.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(teacher.id),
            mocker.ANY,
            900,
        )

    async def test_does_not_hit_db_on_cache_hit(
        self, session: AsyncSession, teacher: User, mocker
    ):
        await UserServiceAdmin.get_teacher_by_id(session, teacher.id)

        mock_repo = mocker.patch.object(UserRepositoryBase, "get_user_by_id")

        await UserServiceAdmin.get_teacher_by_id(session, teacher.id)

        mock_repo.assert_not_called()

    async def test_returns_same_data_on_cache_hit(
        self, session: AsyncSession, teacher: User
    ):
        first = await UserServiceAdmin.get_teacher_by_id(session, teacher.id)
        second = await UserServiceAdmin.get_teacher_by_id(session, teacher.id)

        assert second.id == first.id
        assert second.email == first.email
