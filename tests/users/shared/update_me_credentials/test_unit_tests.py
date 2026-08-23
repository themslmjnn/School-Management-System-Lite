import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.repositories.user import UserRepositoryBase
from src.users.services.shared import UserServiceSelf
from src.users.utils.exceptions import (
    DuplicateEmailChangeRequestError,
    UsernameAlreadyTakenError,
)
from src.users.utils.shared_schemas import UpdateUserCredentials
from utils.exceptions import NoChangesDetectedError
from tests.factories import make_teacher


class TestUpdateMeCredentials:
    async def test_updates_username(self, session: AsyncSession):
        user = await make_teacher(session, username="creds_update_user_1")
        request = UpdateUserCredentials(username="new_username_1")

        await UserServiceSelf.update_me_credentials(session, user.id, request)

        refreshed = await UserRepositoryBase.get_user_by_id(session, user.id)
        assert refreshed.username == "new_username_1"

    async def test_username_change_increments_token_version(
        self, session: AsyncSession
    ):
        user = await make_teacher(session, username="creds_version_user")
        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        version_before = u.session.access_token_version

        await UserServiceSelf.update_me_credentials(
            session, user.id, UpdateUserCredentials(username="creds_version_new")
        )

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
        assert refreshed.session.access_token_version == version_before + 1

    async def test_requests_email_change_stores_pending(
        self, session: AsyncSession, mock_send_email_change_verification
    ):
        user = await make_teacher(session, username="creds_email_user")
        new_email = "new_unique_email@example.com"

        await UserServiceSelf.update_me_credentials(
            session, user.id, UpdateUserCredentials(email=new_email)
        )

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
        assert refreshed.session.pending_new_email == new_email
        assert refreshed.session.email_change_code_hash is not None
        assert refreshed.session.email_change_code_expires_at is not None

    async def test_raises_no_changes_when_same_username(self, session: AsyncSession):
        user = await make_teacher(session, username="creds_same_user")

        with pytest.raises(NoChangesDetectedError):
            await UserServiceSelf.update_me_credentials(
                session, user.id, UpdateUserCredentials(username=user.username)
            )

    async def test_raises_no_changes_when_same_email(self, session: AsyncSession):
        user = await make_teacher(
            session,
            username="creds_same_email",
            email="same_email@example.com",
        )

        with pytest.raises(NoChangesDetectedError):
            await UserServiceSelf.update_me_credentials(
                session, user.id, UpdateUserCredentials(email=user.email)
            )

    async def test_raises_no_changes_when_both_fields_none(self, session: AsyncSession):
        user = await make_teacher(session, username="creds_none_fields")

        with pytest.raises(NoChangesDetectedError):
            await UserServiceSelf.update_me_credentials(
                session, user.id, UpdateUserCredentials()
            )

    async def test_raises_on_duplicate_pending_email_request(
        self, session: AsyncSession, mock_send_email_change_verification
    ):
        user = await make_teacher(session, username="creds_dup_email")
        pending_email = "pending@example.com"
        request = UpdateUserCredentials(email=pending_email)

        await UserServiceSelf.update_me_credentials(session, user.id, request)

        with pytest.raises(DuplicateEmailChangeRequestError):
            await UserServiceSelf.update_me_credentials(session, user.id, request)

    async def test_raises_409_on_duplicate_username(self, session: AsyncSession):
        existing = await make_teacher(session, username="existing_user")
        user = await make_teacher(session, username="creds_conflict")

        with pytest.raises(UsernameAlreadyTakenError):
            await UserServiceSelf.update_me_credentials(
                session, user.id, UpdateUserCredentials(username=existing.username)
            )
