import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from auth.repositories import AuthRepository
from core.security import create_access_token, create_refresh_token, verify_password
from src.auth.schemas import CreateAccessToken, CreateRefreshToken, LoginResponse
from src.core.caching import delete_cache
from src.core.config import settings
from src.core.logging import get_logger
from src.users.repositories import UserRepositoryBase
from src.utils.cache_keys import SessionCacheKey
from src.utils.enums import UserStatus
from utils.constants import HTTP401, HTTP403
from utils.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    EmptyCredentialsError,
    InvalidCredentialsError,
)

logger = get_logger(__name__)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
COOKIE_MAX_AGE = 60 * 60 * 24 * 7


class AuthService:
    @staticmethod
    def _set_refresh_token_cookie(response: Response, raw_refresh_token: str) -> None:
        response.set_cookie(
            key="refresh_token",
            value=raw_refresh_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="strict",
            max_age=COOKIE_MAX_AGE,
            path="/auth/refresh_token",
        )

    @staticmethod
    def _clear_refresh_token_cookie(response: Response) -> None:
        response.delete_cookie(
            key="refresh_token",
            path="/auth/refresh_token",
        )

    @staticmethod
    def _set_refresh_family_cookie(
        response: Response, refresh_token_family: str
    ) -> None:
        response.set_cookie(
            key="refresh_token_family",
            value=refresh_token_family,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="strict",
            max_age=COOKIE_MAX_AGE,
            path="/auth/refresh_token",
        )

    @staticmethod
    def _clear_refresh_family_cookie(response: Response) -> None:
        response.delete_cookie(
            key="refresh_token_family",
            path="/auth/refresh_token",
        )

    @staticmethod
    async def _invalidate_all_tokens(db: AsyncSession, current_user_id: int) -> None:
        user = await UserRepositoryBase.get_user_by_id(
            db, current_user_id, load_session=True
        )
        if user is None:
            return

        user.session.access_token_version += 1
        user.session.refresh_token_hash = None
        user.session.refresh_token_family = None
        user.session.refresh_token_expires_at = None

        await db.commit()

        await delete_cache(SessionCacheKey.access_token_version_key(current_user_id))

        logger.info(
            "tokens_invalidated",
            user_id=current_user_id,
            reason="explicit_invalidation",
        )

    
    @staticmethod
    async def login(
        db: AsyncSession, response: Response, form_data: OAuth2PasswordRequestForm
    ) -> LoginResponse:
        if form_data.username is None or form_data.password is None:
            raise EmptyCredentialsError("Username and password is required")

        user = await AuthRepository.get_user_by_username(
            db, form_data.username, load_session=True, load_login_lockout=True,
        )

        if user is None:
            logger.warning(
                "login_failed",
                reason="user_not_found",
                username=form_data.username,
            )

            raise InvalidCredentialsError(HTTP401.INVALID_CREDENTIALS)

        if (
            user.login_lockout.locked_until
            and datetime.now(UTC) < user.login_lockout.locked_until
        ):
            logger.warning(
                "login_blocked",
                reason="account_locked",
                user_id=user.id,
                locked_until=user.log.locked_until.isoformat(),
            )

            raise AccountLockedError(
                f"Account locked. Try again after {user.login_lockout.locked_until.strftime('%H:%M UTC')}"
            )

        if user.password_hash is None:
            logger.warning(
                "login_failed",
                reason="no_password_set",
                user_id=user.id,
            )

            raise InvalidCredentialsError(HTTP401.INVALID_CREDENTIALS)

        if not verify_password(form_data.password, user.password_hash):
            user.session.failed_login_attempts += 1

            if user.session.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.session.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_MINUTES)

                logger.warning(
                    "account_locked",
                    user_id=user.id,
                    failed_attempts=user.login_lockout.failed_login_attempts,
                    locked_until=user.login_lockout.locked_until.isoformat(),
                )
            else:
                logger.warning(
                    "login_failed",
                    reason="wrong_password",
                    user_id=user.id,
                    failed_attempts=user.login_lockout.failed_login_attempts,
                )

            await db.commit()

            raise InvalidCredentialsError(HTTP401.INVALID_CREDENTIALS)

        if user.status != UserStatus.ACTIVE:
            logger.warning(
                "login_failed",
                reason="account_inactive",
                user_id=user.id,
            )

            raise AccountInactiveError(HTTP403.ACCOUNT_DEACTIVATED)

        user.login_lockout.failed_login_attempts = 0
        user.login_lockout.locked_until = None

        new_family = secrets.token_urlsafe(32)
        user.session.refresh_token_family = new_family

        access_token = create_access_token(
            CreateAccessToken(
                user_id=user.id,
                role=user.role,
                access_token_version=user.session.access_token_version,
            )
        )
        raw_refresh_token, hashed_refresh_token = create_refresh_token(CreateRefreshToken(user_id=user.id))

        user.session.refresh_token_hash = hashed_refresh_token
        user.session.refresh_token_expires_at = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRES_DAYS
        )

        await db.commit()
        await db.refresh(user)

        logger.info(
            "login_success",
            user_id=user.id,
            role=user.role,
        )

        AuthService._set_refresh_token_cookie(response, raw_refresh_token)
        AuthService._set_refresh_family_cookie(response, new_family)

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
    
    @staticmethod
    async def logout(
        response: Response, db: AsyncSession, current_user_id: int
    ) -> None:
        await AuthService._invalidate_all_tokens(db, current_user_id)

        AuthService._clear_refresh_token_cookie(response)
        AuthService._clear_refresh_family_cookie(response)

        logger.info(
            "logout",
            user_id=current_user_id,
        )