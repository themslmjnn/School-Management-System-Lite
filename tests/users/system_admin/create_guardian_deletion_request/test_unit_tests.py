from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from users.utils.exceptions import (
    UserAlreadyPendingDeletionError,
    UserNotFoundError,
)
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from users.services.system_admin import UserServiceAdmin
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.enums import UserStatus
from tests.factories import make_guardian

DELETION_GRACE_PERIOD_DAYS = 30


class TestCreateGuardianDeletionRequest:
    async def test_sets_pending_deletion_state_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        guardian: User,
        mock_send_account_deletion_email,
        mock_delete_cache,
    ):
        await UserServiceAdmin.create_guardian_deletion_request(
            test_db, system_admin.id, guardian.id
        )

        updated_user = await UserRepositoryBase.get_user_by_id(test_db, guardian.id)
        expected = datetime.now(UTC) + timedelta(days=DELETION_GRACE_PERIOD_DAYS)

        assert abs((updated_user.deletion_scheduled_for - expected).total_seconds()) < 5
        assert updated_user.status == UserStatus.PENDING_DELETION
        assert updated_user.is_active is False
        assert updated_user.deletion_scheduled_for is not None

    async def test_resets_session_after_deletion_request(
        self,
        test_db: AsyncSession,
        system_admin: User,
        guardian: User,
        mock_send_account_deletion_email,
        mock_delete_cache,
    ):
        await UserServiceAdmin.create_guardian_deletion_request(
            test_db, system_admin.id, guardian.id
        )

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, guardian.id, load_session=True
        )
        session = user_with_session.session

        assert session.access_token_version == 2
        assert session.refresh_token_hash is None
        assert session.refresh_token_family is None
        assert session.refresh_token_expires_at is None

    async def test_cache_invalidated_including_token_version(
        self,
        test_db: AsyncSession,
        system_admin: User,
        guardian: User,
        mock_send_account_deletion_email,
        mock_delete_cache,
    ):
        await UserServiceAdmin.create_guardian_deletion_request(
            test_db, system_admin.id, guardian.id
        )

        mock_delete_cache.assert_called_once_with(
            SessionCacheKey.access_token_version_key(guardian.id),
            UserCacheKey.user_detail_key_admin(guardian.id),
        )

    async def test_not_found_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_guardian_deletion_request(
                test_db, system_admin.id, 999_999
            )

    async def test_non_guardian_role_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
        teacher: User,
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.create_guardian_deletion_request(
                test_db, system_admin.id, teacher.id
            )

    async def test_already_pending_deletion_raises_error(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )

        with pytest.raises(UserAlreadyPendingDeletionError):
            await UserServiceAdmin.create_guardian_deletion_request(
                test_db, system_admin.id, guardian_pending.id
            )
