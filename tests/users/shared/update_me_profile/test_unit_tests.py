import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.exceptions.exceptions import DuplicatePhoneNumberError, UserNotFoundError
from src.users.models.user import User
from src.users.schemas.user import UpdateMeProfile
from src.users.services.shared import UserServiceSelf
from src.utils.base_exception import AccessDeniedError, NoChangesDetectedError
from src.utils.cache_keys import UserCacheKey
from tests.factories import make_guardian


class TestUpdateMeProfile:
    async def test_guardian_updates_own_profile_fields(
        self, test_db: AsyncSession, guardian: User
    ):
        update_request = UpdateMeProfile(firstname="UpdatedFirst")

        updated = await UserServiceSelf.update_me_profile(
            test_db, guardian.id, update_request
        )

        assert updated.firstname == "Updatedfirst"

    async def test_system_admin_updates_own_profile_fields(
        self, test_db: AsyncSession, system_admin: User
    ):
        update_request = UpdateMeProfile(lastname="UpdatedLast")

        updated = await UserServiceSelf.update_me_profile(
            test_db, system_admin.id, update_request
        )

        assert updated.lastname == "Updatedlast"

    async def test_cache_invalidated(
        self, test_db: AsyncSession, guardian: User, mock_delete_cache_users_shared
    ):
        update_request = UpdateMeProfile(firstname="CacheCheck")

        await UserServiceSelf.update_me_profile(test_db, guardian.id, update_request)

        mock_delete_cache_users_shared.assert_called_once()

    async def test_not_found_raises(self, test_db: AsyncSession):
        update_request = UpdateMeProfile(firstname="Ghost")

        with pytest.raises(UserNotFoundError):
            await UserServiceSelf.update_me_profile(
                test_db, 999_999_999, update_request
            )

    async def test_no_fields_changed_raises_no_changes(
        self, test_db: AsyncSession, guardian: User
    ):
        update_request = UpdateMeProfile(firstname=guardian.firstname)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceSelf.update_me_profile(
                test_db, guardian.id, update_request
            )

    async def test_empty_request_raises_no_changes(
        self, test_db: AsyncSession, guardian: User
    ):
        update_request = UpdateMeProfile()

        with pytest.raises(NoChangesDetectedError):
            await UserServiceSelf.update_me_profile(
                test_db, guardian.id, update_request
            )

    async def test_duplicate_phone_raises_error(
        self, test_db: AsyncSession, guardian: User
    ):
        existing = await make_guardian(test_db, phone_number="+992555111999")
        update_request = UpdateMeProfile(phone_number=existing.phone_number)

        with pytest.raises(DuplicatePhoneNumberError):
            await UserServiceSelf.update_me_profile(
                test_db, guardian.id, update_request
            )

    async def test_cache_invalidated_with_correct_key(
        self, test_db: AsyncSession, guardian: User, mock_delete_cache_users_shared
    ):
        update_request = UpdateMeProfile(firstname="CacheKeyCheck")

        await UserServiceSelf.update_me_profile(test_db, guardian.id, update_request)

        mock_delete_cache_users_shared.assert_called_once_with(
            UserCacheKey.user_detail_key_self(guardian.id)
        )
