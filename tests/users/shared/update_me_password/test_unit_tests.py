import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.repositories.user import UserRepositoryBase
from src.users.schemas.shared import UpdateMePassword
from src.users.services.shared import UserServiceSelf
from src.users.utils.exceptions import IncorrectPasswordError
from tests.factories import make_teacher


class TestUpdateMePassword:
    async def test_updates_password_successfully(
        self, session: AsyncSession, mock_send_password_changed_notification
    ):
        user = await make_teacher(session, username="pwd_update_user")
        request = UpdateMePassword(
            current_password="TestPassword123!",
            new_password="BrandNew456!",
        )

        await UserServiceSelf.update_me_password(session, user.id, request)

        from src.core.security import verify_password

        refreshed = await UserRepositoryBase.get_user_by_id(session, user.id)
        assert (
            await verify_password("TestPassword123!", refreshed.password_hash) is False
        )
        assert await verify_password("BrandNew456!", refreshed.password_hash) is True

    async def test_password_change_invalidates_tokens(
        self, session: AsyncSession, mock_send_password_changed_notification
    ):
        user = await make_teacher(session, username="pwd_tokens_user")

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        version_before = u.session.access_token_version

        await UserServiceSelf.update_me_password(
            session,
            user.id,
            UpdateMePassword(
                current_password="TestPassword123!",
                new_password="BrandNew456!",
            ),
        )

        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
        assert refreshed.session.access_token_version == version_before + 1
        assert refreshed.session.refresh_token_hash is None
        assert refreshed.session.refresh_token_family is None

    async def test_raises_on_incorrect_current_password(self, session: AsyncSession):
        user = await make_teacher(session, username="pwd_wrong_user")

        with pytest.raises(IncorrectPasswordError):
            await UserServiceSelf.update_me_password(
                session,
                user.id,
                UpdateMePassword(
                    current_password="WrongPassword!",
                    new_password="BrandNew456!",
                ),
            )

    async def test_raises_422_on_weak_new_password(self):
        with pytest.raises(ValidationError):
            UpdateMePassword(current_password="TestPassword123!", new_password="weak")
