from sqlalchemy.ext.asyncio import AsyncSession

from auth.service import AuthService
from tests.conftest import user_form
from tests.factories import make_teacher
from users.repositories.user import UserRepositoryBase


class TestLogout:
    async def test_logout_clears_refresh_token_from_session(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(session, username="logout_user")
        form = user_form(username=user.username, password="TestPassword123!")
        await AuthService.login(session, mock_response, form)
 
        await AuthService.logout(mock_response, session, user.id)
 
        refreshed = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
 
        assert refreshed.session.refresh_token_hash is None
        assert refreshed.session.refresh_token_family is None
        assert refreshed.session.refresh_token_expires_at is None
 
    async def test_logout_increments_access_token_version(
        self, session: AsyncSession, mock_response
    ):
        user = await make_teacher(session, username="logout_version_user")
 
        before = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
        version_before = before.session.access_token_version
 
        await AuthService.logout(mock_response, session, user.id)
 
        after = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
 
        assert after.session.access_token_version == version_before + 1
 
    async def test_logout_clears_cookies(self, session: AsyncSession, mock_response):
        user = await make_teacher(session, username="logout_cookie_user")
        response = mock_response
 
        await AuthService.logout(response, session, user.id)
 
        response.delete_cookie.assert_called()
        deleted_keys = [
            call.kwargs["key"] for call in response.delete_cookie.call_args_list
        ]
        assert "refresh_token" in deleted_keys
        assert "refresh_token_family" in deleted_keys
 
    async def test_logout_of_nonexistent_user_does_not_raise(
        self, session: AsyncSession, mock_response
    ):
        await AuthService.logout(mock_response, session, 999_999)
 