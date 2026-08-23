from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.service import AuthService
from src.users.models.user import User
from src.users.repositories.user import UserRepositoryBase
from src.utils.exceptions import InvalidRefreshTokenError
from tests.conftest import mock_response, user_form
from tests.factories import make_teacher


class TestRefreshToken:
    async def _login_and_capture_tokens(
        self, session: AsyncSession, mock_response, student: User
    ) -> tuple[str, str]:
        form = user_form(username=student.username, password="TestPassword123!")
        await AuthService.login(session, mock_response, form)

        u = await UserRepositoryBase.get_user_by_id(
            session, student.id, load_session=True
        )

        return u.session.refresh_token_family

    async def test_raises_when_token_not_in_db(self, session: AsyncSession):
        user = await make_teacher(session, username="rt_no_db_user")
        form = user_form(username=user.username, password="TestPassword123!")

        raw_token = None
        family = None

        def capture_cookie(**kwargs):
            nonlocal raw_token, family
            if kwargs.get("key") == "refresh_token":
                raw_token = kwargs["value"]
            elif kwargs.get("key") == "refresh_token_family":
                family = kwargs["value"]

        response = MagicMock()
        response.set_cookie.side_effect = capture_cookie

        await AuthService.login(session, response, form)

        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)
        u.session.refresh_token_hash = None
        await session.commit()

        with pytest.raises(InvalidRefreshTokenError):
            await AuthService.refresh_token(session, mock_response, raw_token, family)

    async def test_raises_for_invalid_jwt(self, session: AsyncSession):
        await make_teacher(session, username="rt_invalid_jwt_user")

        with pytest.raises((InvalidRefreshTokenError, Exception)):
            await AuthService.refresh_token(
                session, mock_response, "not.a.real.jwt", "some_family"
            )

    async def test_raises_for_wrong_family(self, session: AsyncSession):
        user = await make_teacher(session, username="rt_wrong_family_user")
        form = user_form(username=user.username, password="TestPassword123!")

        raw_token = None

        def capture(**kwargs):
            nonlocal raw_token
            if kwargs.get("key") == "refresh_token":
                raw_token = kwargs["value"]

        response = MagicMock()
        response.set_cookie.side_effect = capture
        await AuthService.login(session, response, form)

        with pytest.raises(InvalidRefreshTokenError):
            await AuthService.refresh_token(
                session, mock_response, raw_token, "wrong_family_value"
            )

    async def test_successful_rotation_returns_new_access_token(
        self, session: AsyncSession
    ):
        user = await make_teacher(session, username="rt_rotate_user")
        form = user_form(username=user.username, password="TestPassword123!")

        raw_token = None
        family = None

        def capture(**kwargs):
            nonlocal raw_token, family
            if kwargs.get("key") == "refresh_token":
                raw_token = kwargs["value"]
            elif kwargs.get("key") == "refresh_token_family":
                family = kwargs["value"]

        response = MagicMock()
        response.set_cookie.side_effect = capture
        await AuthService.login(session, response, form)

        result = await AuthService.refresh_token(
            session, MagicMock(), raw_token, family
        )

        assert result.access_token is not None
        assert result.token_type == "bearer"

    async def test_rotation_replaces_stored_token_hash(self, session: AsyncSession):
        user = await make_teacher(session, username="rt_hash_replace_user")
        form = user_form(username=user.username, password="TestPassword123!")

        raw_token = None
        family = None

        def capture(**kwargs):
            nonlocal raw_token, family
            if kwargs.get("key") == "refresh_token":
                raw_token = kwargs["value"]
            elif kwargs.get("key") == "refresh_token_family":
                family = kwargs["value"]

        response = MagicMock()
        response.set_cookie.side_effect = capture
        await AuthService.login(session, response, form)

        u_before = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )
        old_hash = u_before.session.refresh_token_hash

        await AuthService.refresh_token(session, MagicMock(), raw_token, family)

        u_after = await UserRepositoryBase.get_user_by_id(
            session, user.id, load_session=True
        )

        assert u_after.session.refresh_token_hash != old_hash

    async def test_token_reuse_invalidates_all_tokens(self, session: AsyncSession):
        """Using a consumed token (family mismatch after rotation) must
        invalidate everything — this is the token theft detection path."""
        user = await make_teacher(session, username="rt_reuse_user")
        form = user_form(username=user.username, password="TestPassword123!")

        raw_token = None
        family = None

        def capture(**kwargs):
            nonlocal raw_token, family
            if kwargs.get("key") == "refresh_token":
                raw_token = kwargs["value"]
            elif kwargs.get("key") == "refresh_token_family":
                family = kwargs["value"]

        response = MagicMock()
        response.set_cookie.side_effect = capture
        await AuthService.login(session, response, form)

        # First rotation — consumes the token, rotates family
        await AuthService.refresh_token(session, MagicMock(), raw_token, family)

        # Re-using the original token with the original family triggers theft detection
        with pytest.raises(InvalidRefreshTokenError):
            await AuthService.refresh_token(session, MagicMock(), raw_token, family)

        # Session must now be fully invalidated
        u = await UserRepositoryBase.get_user_by_id(session, user.id, load_session=True)

        assert u.session.refresh_token_hash is None
        assert u.session.refresh_token_family is None
