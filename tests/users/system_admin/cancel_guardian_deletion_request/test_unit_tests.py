import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from users.utils.exceptions import UserNotFoundError
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from users.services.system_admin import UserServiceAdmin
from src.utils.cache_keys import UserCacheKey
from src.utils.enums import UserStatus
from tests.factories import make_guardian


class TestCancelGuardianDeletionRequest:
    async def test_cancels_deletion_successfully(
        self,
        test_db: AsyncSession,
        system_admin: User,
        mock_send_account_deletion_canceled_email,
        mock_delete_cache,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )

        await UserServiceAdmin.cancel_guardian_deletion_request(
            test_db, system_admin.id, guardian_pending.id
        )

        updated_user = await UserRepositoryBase.get_user_by_id(
            test_db, guardian_pending.id
        )

        assert updated_user.status != UserStatus.PENDING_DELETION

    async def test_cache_invalidated_after_cancellation(
        self,
        test_db: AsyncSession,
        system_admin: User,
        mock_send_account_deletion_canceled_email,
        mock_delete_cache,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )

        await UserServiceAdmin.cancel_guardian_deletion_request(
            test_db, system_admin.id, guardian_pending.id
        )

        mock_delete_cache.assert_called_once_with(
            UserCacheKey.user_detail_key_admin(guardian_pending.id),
        )

    async def test_not_found_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.cancel_guardian_deletion_request(
                test_db, system_admin.id, 999_999
            )

    async def test_non_pending_guardian_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
        guardian: User,
    ):
        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.cancel_guardian_deletion_request(
                test_db, system_admin.id, guardian.id
            )

    async def test_lost_race_raises_user_not_found(
        self,
        test_db: AsyncSession,
        system_admin: User,
        mocker,
    ):
        guardian_pending = await make_guardian(
            test_db, status=UserStatus.PENDING_DELETION, is_active=False
        )

        mocker.patch(
            "src.users.services.system_admin.user.UserRepositoryBase.reactivate_pending_deletion_user",
            return_value=False,
        )

        with pytest.raises(UserNotFoundError):
            await UserServiceAdmin.cancel_guardian_deletion_request(
                test_db, system_admin.id, guardian_pending.id
            )
