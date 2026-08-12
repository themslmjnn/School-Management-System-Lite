import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from users.utils.exceptions import UserNotFoundError
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from users.services.system_admin import UserServiceAdmin
from src.utils.cache_keys import UserCacheKey
from src.utils.enums import UserRole
from tests.factories import (
    make_student,
    make_system_admin,
    make_teacher,
)


class TestGetGuardianById:
    async def test_returns_correct_data(self, test_db: AsyncSession, guardian: User):
        result = await UserServiceAdmin.get_guardian_by_id(test_db, guardian.id)

        assert result.id == guardian.id
        assert result.email == guardian.email
        assert result.role == UserRole.GUARDIAN

    async def test_returns_404_when_not_found(self, test_db: AsyncSession):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.get_guardian_by_id(test_db, 999_999)

    @pytest.mark.parametrize(
        "factory",
        [make_teacher, make_student, make_system_admin],
    )
    async def test_returns_404_for_non_guardian_role(
        self, test_db: AsyncSession, factory
    ):
        non_guardian = await factory(test_db)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.get_guardian_by_id(test_db, non_guardian.id)

    async def test_populates_cache_after_db_hit(
        self, test_db: AsyncSession, guardian: User, mock_set_cache, mocker
    ):
        await UserServiceAdmin.get_guardian_by_id(test_db, guardian.id)

        mock_set_cache.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(guardian.id),
            mocker.ANY,
            900,
        )

    async def test_does_not_hit_db_on_cache_hit(
        self, test_db: AsyncSession, guardian: User, mocker
    ):
        await UserServiceAdmin.get_guardian_by_id(test_db, guardian.id)

        mock_repo = mocker.patch.object(UserRepositoryBase, "get_user_by_id")

        await UserServiceAdmin.get_guardian_by_id(test_db, guardian.id)

        mock_repo.assert_not_called()

    async def test_returns_same_data_on_cache_hit(
        self, test_db: AsyncSession, guardian: User
    ):
        first = await UserServiceAdmin.get_guardian_by_id(test_db, guardian.id)
        second = await UserServiceAdmin.get_guardian_by_id(test_db, guardian.id)

        assert second.id == first.id
        assert second.email == first.email
