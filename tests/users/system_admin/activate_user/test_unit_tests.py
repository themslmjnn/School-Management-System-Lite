import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.users.services.system_admin import UserServiceAdmin
from src.users.utils.exceptions import (
    UserAlreadyActiveError,
    UserNotFoundError,
)
from src.utils.cache_keys import UserCacheKey
from src.utils.enums import UserRole, UserStatus
from tests.factories import make_deactivated_user


class TestActivateUser:
    async def test_activate_user_successfully(
        self,
        session: AsyncSession,
        system_admin: User,
        mock_send_account_activation_email,
        mock_delete_cache_users_system_admin,
    ):
        deactivated = await make_deactivated_user(session)

        await UserServiceAdmin.activate_user(session, system_admin.id, deactivated.id)

        activated_user = await UserRepositoryBase.get_user_by_id(
            session, deactivated.id, load_login_lockout=True
        )

        assert activated_user.is_active is True
        assert activated_user.status == UserStatus.ACTIVE
        assert activated_user.login_lockout.failed_login_attempts == 0
        assert activated_user.login_lockout.locked_until is None

    async def test_activate_user_invalidates_cache(
        self,
        session: AsyncSession,
        system_admin: User,
        mock_send_account_activation_email,
        mock_delete_cache_users_system_admin,
    ):
        deactivated = await make_deactivated_user(session)

        await UserServiceAdmin.activate_user(session, system_admin.id, deactivated.id)

        mock_delete_cache_users_system_admin.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(deactivated.id)
        )

    async def test_activate_user_not_found(
        self, session: AsyncSession, system_admin: User
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.activate_user(session, system_admin.id, 999_999)

    async def test_activate_already_active_user(
        self, session: AsyncSession, system_admin: User, teacher: User
    ):
        with pytest.raises(UserAlreadyActiveError):
            await UserServiceAdmin.activate_user(session, system_admin.id, teacher.id)

    async def test_activate_user_excludes_system_admins(
        self, session: AsyncSession, system_admin: User
    ):
        other_admin = await make_deactivated_user(session, role=UserRole.SYSTEM_ADMIN)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.activate_user(
                session, system_admin.id, other_admin.id
            )
