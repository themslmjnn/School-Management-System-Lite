import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from users.utils.exceptions import (
    UserAlreadyInactiveError,
    UserNotFoundError,
)
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from users.services.system_admin import UserServiceAdmin
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.enums import UserStatus
from tests.factories import make_deactivated_user, make_system_admin


class TestDeactivateUser:
    async def test_deactivate_user_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_delete_cache,
    ):
        await UserServiceAdmin.deactivate_user(test_db, system_admin.id, teacher.id)

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )

        assert user_with_session.is_active is False
        assert user_with_session.status == UserStatus.DEACTIVATED
        assert user_with_session.session.access_token_version == 2
        assert user_with_session.session.refresh_token_hash is None
        assert user_with_session.session.refresh_token_family is None
        assert user_with_session.session.refresh_token_expires_at is None

    async def test_deactivate_user_invalidates_cache(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
        mock_send_account_deactivation_email,
        mock_delete_cache,
    ):
        await UserServiceAdmin.deactivate_user(test_db, system_admin.id, teacher.id)

        mock_delete_cache.assert_called_once_with(
            SessionCacheKey.access_token_version_key(teacher.id),
            UserCacheKey.user_detail_key_admin(teacher.id),
            UserCacheKey.user_detail_key_staff(teacher.id),
            UserCacheKey.user_detail_key_self(teacher.id),
        )

    async def test_deactivate_user_not_found(
        self, test_db: AsyncSession, system_admin: User
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.deactivate_user(test_db, system_admin.id, 999_999)

    async def test_deactivate_already_inactive_user(
        self, test_db: AsyncSession, system_admin: User
    ):
        deactivated = await make_deactivated_user(test_db)

        with pytest.raises(UserAlreadyInactiveError):
            await UserServiceAdmin.deactivate_user(
                test_db, system_admin.id, deactivated.id
            )

    async def test_deactivate_user_excludes_system_admins(
        self, test_db: AsyncSession, system_admin: User
    ):
        other_admin = await make_system_admin(test_db)

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.deactivate_user(
                test_db, system_admin.id, other_admin.id
            )
