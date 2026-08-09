from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.exceptions.exceptions import (
    DuplicateEmailChangeRequestError,
    UsernameAlreadyTakenError,
    UserNotFoundError,
)
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from users.schemas.system_admin.user import UpdateMeCredentials
from src.users.services.shared import UserServiceSelf
from src.utils.base_exception import NoChangesDetectedError
from src.utils.cache_keys import SessionCacheKey
from tests.factories import make_teacher


class TestUpdateMeCredentials:
    async def test_username_updated_immediately(
        self, test_db: AsyncSession, teacher: User
    ):
        update_request = UpdateMeCredentials(username="new_self_username")

        await UserServiceSelf.update_me_credentials(test_db, teacher.id, update_request)

        updated = await UserRepositoryBase.get_user_by_id(test_db, teacher.id)

        assert updated.username == "new_self_username"

    async def test_email_change_does_not_apply_immediately(
        self, test_db: AsyncSession, teacher: User
    ):
        original_email = teacher.email
        update_request = UpdateMeCredentials(email="pending.change@example.com")

        await UserServiceSelf.update_me_credentials(test_db, teacher.id, update_request)

        updated = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )

        assert updated.email == original_email
        assert updated.session.pending_new_email == "pending.change@example.com"
        assert updated.session.email_change_code_hash is not None
        assert updated.session.email_change_code_expires_at is not None

    async def test_email_unchanged_when_same_as_current(
        self, test_db: AsyncSession, teacher: User
    ):
        update_request = UpdateMeCredentials(email=teacher.email)

        with pytest.raises(NoChangesDetectedError):
            await UserServiceSelf.update_me_credentials(
                test_db, teacher.id, update_request
            )

        updated = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )
        assert updated.session.pending_new_email is None

    async def test_duplicate_username_raises(
        self, test_db: AsyncSession, teacher: User
    ):
        await make_teacher(test_db, username="self_taken_username")
        update_request = UpdateMeCredentials(username="self_taken_username")

        with pytest.raises(UsernameAlreadyTakenError):
            await UserServiceSelf.update_me_credentials(
                test_db, teacher.id, update_request
            )

    async def test_not_found_raises(self, test_db: AsyncSession):
        update_request = UpdateMeCredentials(username="doesntmatter123")

        with pytest.raises(UserNotFoundError):
            await UserServiceSelf.update_me_credentials(
                test_db, 999_999_999, update_request
            )

    async def test_no_fields_raises_no_changes(
        self, test_db: AsyncSession, teacher: User
    ):
        update_request = UpdateMeCredentials()

        with pytest.raises(NoChangesDetectedError):
            await UserServiceSelf.update_me_credentials(
                test_db, teacher.id, update_request
            )

    async def test_same_values_raise_no_changes(
        self, test_db: AsyncSession, teacher: User
    ):
        update_request = UpdateMeCredentials(
            username=teacher.username, email=teacher.email
        )

        with pytest.raises(NoChangesDetectedError):
            await UserServiceSelf.update_me_credentials(
                test_db, teacher.id, update_request
            )

    async def test_username_change_increments_session_version(
        self, test_db: AsyncSession, teacher: User
    ):
        update_request = UpdateMeCredentials(username="new_version_username")

        await UserServiceSelf.update_me_credentials(test_db, teacher.id, update_request)

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )
        assert user_with_session.session.access_token_version == 2

    async def test_email_only_change_does_not_increment_session_version(
        self, test_db: AsyncSession, teacher: User
    ):
        update_request = UpdateMeCredentials(email="pending.only@example.com")

        await UserServiceSelf.update_me_credentials(test_db, teacher.id, update_request)

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )
        assert user_with_session.session.access_token_version == 1

    async def test_username_change_invalidates_token_version_cache(
        self, test_db: AsyncSession, teacher: User, mocker
    ):
        calls = []

        async def capture_delete_cache(*args):
            calls.extend(args)

        mocker.patch(
            "src.users.services.shared.delete_cache",
            side_effect=capture_delete_cache,
        )

        update_request = UpdateMeCredentials(username="cache_check_username")
        await UserServiceSelf.update_me_credentials(test_db, teacher.id, update_request)

        assert SessionCacheKey.access_token_version_key(teacher.id) in calls

    async def test_email_only_does_not_invalidate_token_version_cache(
        self, test_db: AsyncSession, teacher: User, mocker
    ):
        calls = []

        async def capture_delete_cache(*args):
            calls.extend(args)

        mocker.patch(
            "src.users.services.shared.delete_cache",
            side_effect=capture_delete_cache,
        )

        update_request = UpdateMeCredentials(email="email.cache@example.com")
        await UserServiceSelf.update_me_credentials(test_db, teacher.id, update_request)

        assert SessionCacheKey.access_token_version_key(teacher.id) not in calls

    async def test_duplicate_pending_email_request_raises(
        self, test_db: AsyncSession, teacher: User
    ):
        update_request = UpdateMeCredentials(email="duplicate.pending@example.com")
        await UserServiceSelf.update_me_credentials(test_db, teacher.id, update_request)

        with pytest.raises(DuplicateEmailChangeRequestError):
            await UserServiceSelf.update_me_credentials(
                test_db, teacher.id, update_request
            )

    async def test_expired_pending_code_allows_re_request(
        self, test_db: AsyncSession, teacher: User
    ):
        update_request = UpdateMeCredentials(email="resubmit.after.expiry@example.com")
        await UserServiceSelf.update_me_credentials(test_db, teacher.id, update_request)

        user_with_session = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )
        user_with_session.session.email_change_code_expires_at = datetime.now(
            UTC
        ) - timedelta(minutes=1)
        await test_db.commit()

        await UserServiceSelf.update_me_credentials(test_db, teacher.id, update_request)

        updated = await UserRepositoryBase.get_user_by_id(
            test_db, teacher.id, load_session=True
        )
        assert updated.session.pending_new_email == "resubmit.after.expiry@example.com"
