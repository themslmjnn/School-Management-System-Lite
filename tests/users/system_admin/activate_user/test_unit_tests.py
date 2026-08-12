import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from users.utils.exceptions import (
    UserAlreadyActiveError,
    UserNotFoundError,
)
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from users.services.system_admin import UserServiceAdmin
from src.utils.cache_keys import UserCacheKey
from src.utils.enums import UserRole, UserStatus
from tests.factories import make_deactivated_user


class TestActivateUser:
    async def test_activate_user_successfully(
        self, test_db: AsyncSession, system_admin: User, mock_delete_cache
    ):
        deactivated = await make_deactivated_user(test_db)

        await UserServiceAdmin.activate_user(test_db, system_admin.id, deactivated.id)

        activated_user = await UserRepositoryBase.get_user_by_id(
            test_db, deactivated.id, load_login_lockout=True
        )

        assert activated_user.is_active is True
        assert activated_user.status == UserStatus.ACTIVE
        assert activated_user.login_lockout.failed_login_attempts == 0
        assert activated_user.login_lockout.locked_until is None

    async def test_activate_user_invalidates_cache(
        self,
        test_db: AsyncSession,
        system_admin: User,
        mock_send_account_activation_email,
        mock_delete_cache,
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
