import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.exceptions.exceptions import UserNotFoundError
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.users.services.system_admin.user import UserServiceAdmin
from src.utils.cache_keys import UserCacheKey
from src.utils.enums import UserRole
from tests.factories import (
    make_director,
    make_guardian,
    make_student,
    make_system_admin,
)


class TestGetStaffById:
    async def test_returns_correct_data(self, test_db: AsyncSession, teacher: User):
        result = await UserServiceAdmin.get_staff_by_id(test_db, teacher.id)

        assert result.id == teacher.id
        assert result.email == teacher.email
        assert result.role == UserRole.TEACHER

    async def test_returns_404_when_not_found(self, test_db):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.get_staff_by_id(test_db, 999_999)

    @pytest.mark.parametrize(
        "factory",
        [make_student, make_guardian, make_director, make_system_admin],
    )
    async def test_returns_404_for_non_staff_role(self, test_db: AsyncSession, factory):
        non_staff = await factory(test_db)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.get_staff_by_id(test_db, non_staff.id)

    async def test_populates_cache_after_db_hit(
        self, test_db: AsyncSession, teacher: User, mock_set_cache, mocker
    ):
        await UserServiceAdmin.get_staff_by_id(test_db, teacher.id)

        mock_set_cache.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(teacher.id),
            mocker.ANY,
            900,
        )

    async def test_does_not_hit_db_on_cache_hit(
        self, test_db: AsyncSession, teacher: User, mocker
    ):
        await UserServiceAdmin.get_staff_by_id(test_db, teacher.id)

        mock_repo = mocker.patch.object(UserRepositoryBase, "get_user_by_id")

        await UserServiceAdmin.get_staff_by_id(test_db, teacher.id)

        mock_repo.assert_not_called()

    async def test_returns_same_data_on_cache_hit(
        self, test_db: AsyncSession, teacher: User
    ):
        first = await UserServiceAdmin.get_staff_by_id(test_db, teacher.id)
        second = await UserServiceAdmin.get_staff_by_id(test_db, teacher.id)

        assert second.id == first.id
        assert second.email == first.email
