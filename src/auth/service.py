import asyncio
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.repository import AuthRepository
from src.auth.schemas import (
    ActivateAccountWithToken,
    CreateAccessToken,
    CreateRefreshToken,
    ForgotPasswordPublicRequest,
    LoginResponse,
    ResetPassword,
)
from src.core.caching import delete_cache
from src.core.config import settings
from src.core.logging import get_logger
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_reset_password_token,
    hash_password,
    verify_invite_token,
    verify_password,
    verify_refresh_token,
    verify_reset_password_token,
)
from src.users.repositories.users import UserRepositoryBase
from src.utils import email as email_sender
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.constants import HTTP400, HTTP401, HTTP403
from src.utils.enums import EmailType, UserStatus
from src.utils.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    EmptyCredentialsError,
    ExpiredInviteTokenError,
    ExpiredRefreshTokenError,
    ExpiredResetPasswordTokenError,
    InvalidCredentialsError,
    InvalidInviteTokenError,
    InvalidRefreshTokenError,
    InvalidResetPasswordTokenError,
)
from src.utils.response_messages import PublicMessages
from src.utils.response_schema import MessageResponse

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
            db,
            form_data.username,
            load_session=True,
            load_login_lockout=True,
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
                locked_until=user.login_lockout.locked_until.isoformat(),
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

        if user.status == UserStatus.PENDING_ACTIVATION:
            logger.warning(
                "login_failed",
                reason="account_not_activated",
                user_id=user.id,
            )
            raise InvalidCredentialsError(HTTP401.INVALID_CREDENTIALS)

        if not await verify_password(form_data.password, user.password_hash):
            user.login_lockout.failed_login_attempts += 1

            if user.login_lockout.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.login_lockout.locked_until = datetime.now(UTC) + timedelta(
                    minutes=LOCKOUT_MINUTES
                )

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

        if user.status == UserStatus.PENDING_DELETION:
            grace_period_active = (
                user.deletion_scheduled_for is not None
                and datetime.now(UTC) < user.deletion_scheduled_for
            )

            if not grace_period_active:
                logger.warning(
                    "login_failed",
                    reason="deletion_grace_period_expired",
                    user_id=user.id,
                )

                raise AccountInactiveError(HTTP403.ACCOUNT_DEACTIVATED)

            reactivated = await UserRepositoryBase.reactivate_pending_deletion_user(
                db, user.id
            )

            if not reactivated:
                await db.rollback()

                logger.warning(
                    "login_reactivation_lost_race",
                    user_id=user.id,
                    denial_reason="user_hard_deleted_before_reactivation_committed",
                )

                raise AccountInactiveError(HTTP403.ACCOUNT_DEACTIVATED)

            logger.info("account_reactivated_on_login", user_id=user.id)

            user_email = user.email

            asyncio.create_task(
                email_sender.send_safe(
                    email_sender.send_account_deletion_canceled_email(user_email),
                    email_type=EmailType.CANCEL_ACCOUNT_DELETION,
                )
            )

            await delete_cache(UserCacheKey.user_detail_key_admin(user.id))

        elif user.status != UserStatus.ACTIVE:
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
        raw_refresh_token, hashed_refresh_token = create_refresh_token(
            CreateRefreshToken(user_id=user.id)
        )

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

    @staticmethod
    async def activate_account_with_token(
        db: AsyncSession, activation_request: ActivateAccountWithToken
    ) -> None:
        user = await AuthRepository.get_user_by_username(
            db, activation_request.username, load_activation=True
        )

        if user is None or user.activation.invite_token_hash is None:
            logger.warning(
                "activation_failed",
                reason="invalid_invite_token",
                email=activation_request.email,
            )

            raise InvalidInviteTokenError(HTTP400.INVALID_INVITE_TOKEN)

        if (
            user.activation.invite_token_expires_at is None
            or datetime.now(UTC) > user.activation.invite_token_expires_at
        ):
            logger.warning(
                "activation_failed",
                reason="invite_token_expired",
                user_id=user.id,
            )

            raise ExpiredInviteTokenError(HTTP400.EXPIRED_INVITE_TOKEN)

        if not verify_invite_token(
            activation_request.invite_token, user.activation.invite_token_hash
        ):
            logger.warning(
                "activation_failed",
                reason="invite_token_mismatch",
                user_id=user.id,
            )

            raise InvalidInviteTokenError(HTTP400.INVALID_INVITE_TOKEN)

        user.password_hash = await hash_password(activation_request.new_password)
        user.is_active = True
        user.status = UserStatus.ACTIVE
        user.activation.invite_token_hash = None
        user.activation.invite_token_expires_at = None

        await db.commit()
        await db.refresh(user)

        logger.info(
            "account_activated",
            user_id=user.id,
            method="invite_token",
        )

    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        response: Response,
        raw_refresh_token: str,
        refresh_token_family: str,
    ) -> LoginResponse:
        try:
            payload = decode_refresh_token(raw_refresh_token)
            user_id = int(payload.get("sub"))

        except ExpiredSignatureError as e:
            logger.warning(
                "refresh_token_rotation_failed",
                reason="token_expired",
            )
            raise ExpiredRefreshTokenError(HTTP401.EXPIRED_REFRESH_TOKEN) from e

        except (ValueError, TypeError) as e:
            logger.warning(
                "invalid_jwt",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise InvalidRefreshTokenError(HTTP401.INVALID_REFRESH_TOKEN) from e

        user = await UserRepositoryBase.get_user_by_id(db, user_id, load_session=True)

        if (
            user is None
            or user.session.refresh_token_hash is None
            or user.session.refresh_token_family is None
            or user.session.refresh_token_expires_at is None
        ):
            logger.warning(
                "refresh_token_rotation_failed",
                reason="invalid_refresh_token",
                user_id=user_id,
            )
            raise InvalidRefreshTokenError(HTTP401.INVALID_REFRESH_TOKEN)

        if datetime.now(UTC) > user.session.refresh_token_expires_at:
            logger.warning(
                "refresh_token_rotation_failed",
                reason="refresh_token_expired",
                user_id=user.id,
            )
            raise ExpiredRefreshTokenError(HTTP401.EXPIRED_REFRESH_TOKEN)

        refresh_token_family_valid = hmac.compare_digest(
            refresh_token_family, user.session.refresh_token_family
        )
        refresh_token_hash_valid = verify_refresh_token(
            raw_refresh_token, user.session.refresh_token_hash
        )

        if not refresh_token_family_valid or not refresh_token_hash_valid:
            await AuthService._invalidate_all_tokens(db, user.id)

            logger.warning(
                "refresh_token_security_violation",
                user_id=user.id,
                refresh_token_family_valid=refresh_token_family_valid,
                refresh_token_hash_valid=refresh_token_hash_valid,
                action="all_tokens_invalidated",
            )

            raise InvalidRefreshTokenError(HTTP401.INVALID_REFRESH_TOKEN)

        new_family = secrets.token_urlsafe(32)
        user.session.refresh_token_family = new_family

        access_token = create_access_token(
            CreateAccessToken(
                user_id=user.id,
                role=user.role,
                access_token_version=user.session.access_token_version,
            )
        )
        raw_refresh_token, hashed_refresh_token = create_refresh_token(
            CreateRefreshToken(user_id=user.id)
        )

        user.session.refresh_token_hash = hashed_refresh_token
        user.session.refresh_token_expires_at = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRES_DAYS
        )

        await db.commit()
        await db.refresh(user)

        logger.info(
            "refresh_token_rotated",
            user_id=user.id,
            method="refresh_token",
        )

        AuthService._set_refresh_token_cookie(response, raw_refresh_token)
        AuthService._set_refresh_family_cookie(response, new_family)

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    @staticmethod
    async def reset_password(db: AsyncSession, update_request: ResetPassword):
        user = await AuthRepository.get_user_by_username(
            db,
            update_request.username,
            load_session=True,
            load_login_lockout=True,
        )

        if user is None:
            logger.warning(
                "password_reset_failed",
                reason="user_not_found",
                target_username=update_request.username,
            )

            raise InvalidCredentialsError(HTTP401.INVALID_CREDENTIALS)

        if (
            user.session.reset_password_token_expires_at is None
            or datetime.now(UTC) > user.session.reset_password_token_expires_at
        ):
            logger.warning(
                "reset_password_failed",
                reason="reset_password_token_expired",
                user_id=user.id,
            )

            raise ExpiredResetPasswordTokenError(HTTP400.EXPIRED_RESET_PASSWORD_TOKEN)

        if not verify_reset_password_token(
            update_request.reset_token, user.session.reset_password_token_hash
        ):
            logger.warning(
                "reset_password_failed",
                reason="invalid_reset_password_token",
                target_username=update_request.username,
            )

            raise InvalidResetPasswordTokenError(HTTP400.INVALID_RESET_PASSWORD_TOKEN)

        user.password_hash = await hash_password(update_request.new_password)
        user.session.reset_password_token_hash = None
        user.session.reset_password_token_expires_at = None
        user.session.access_token_version += 1
        user.session.refresh_token_hash = None
        user.session.refresh_token_expires_at = None
        user.session.refresh_token_family = None

        user.login_lockout.failed_login_attempts = 0
        user.login_lockout.locked_until = None

        await db.commit()
        await db.refresh(user)

        await delete_cache(SessionCacheKey.access_token_version_key(user.id))

        logger.info(
            "password_changed",
            user_id=user.id,
        )

    @staticmethod
    async def create_forgot_password_request(
        db: AsyncSession,
        forgot_password_request: ForgotPasswordPublicRequest,
    ) -> MessageResponse:
        user = await AuthRepository.get_user_by_username(
            db, forgot_password_request.username, load_session=True
        )

        raw_reset_password_token, hashed_reset_password_token = (
            generate_reset_password_token()
        )

        if user is not None and user.session is not None:
            user.session.reset_password_token_hash = hashed_reset_password_token
            user.session.reset_password_token_expires_at = datetime.now(
                UTC
            ) + timedelta(minutes=settings.RESET_PASSWORD_EXPIRES_MINUTES)

            await db.commit()

            asyncio.create_task(
                email_sender.send_safe(
                    email_sender.send_forgot_password_email(
                        user.email, raw_reset_password_token
                    ),
                    email_type=EmailType.FORGOT_PASSWORD,
                )
            )

            logger.info(
                "forgot_password_request_processed",
                user_id=user.id,
            )

        return MessageResponse(detail=PublicMessages.FORGOT_PASSWORD)
