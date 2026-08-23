import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.advisory_locks import acquire_student_contact_lock
from src.core.caching import delete_cache, get_cache, set_cache
from src.core.config import settings
from src.core.dependencies import CurrentUser
from src.core.logging import get_logger
from src.core.security import (
    generate_email_change_code,
    hash_password,
    verify_email_change_code,
    verify_password,
)
from src.users.repositories.user import UserRepositoryBase
from src.users.schemas.shared import (
    ConfirmEmailChange,
    StudentResponseSelf,
    StudentResponseSelfCache,
    UpdateMePassword,
    UserResponseSelf,
    UserResponseSelfCache,
)
from src.users.services.system_admin import check_contact_limit
from src.users.utils.constants import HTTP404, STUDENT_MAX_SHARED_CONTACT
from src.users.utils.exceptions import (
    DuplicateEmailChangeRequestError,
    EmailChangeCodeExpiredError,
    IncorrectPasswordError,
    InvalidEmailChangeCodeError,
    NoPendingEmailChangeError,
    UserNotFoundError,
    handle_non_student_unique_contact_error,
    handle_username_integrity_error,
)
from src.users.utils.shared_schemas import UpdateUserCredentials
from src.utils import email as email_sender
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.constants import HTTP400
from src.utils.enums import EmailType, UserRole
from src.utils.exceptions import (
    NoChangesDetectedError,
    raise_unhandled_integrity_error,
)
from src.utils.helpers import ensure_exists

logger = get_logger(__name__)


class UserServiceSelf:
    @staticmethod
    async def get_my_profile(
        session: AsyncSession, current_user: CurrentUser
    ) -> UserResponseSelf:
        cache_key = UserCacheKey.user_detail_key_self(current_user.id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = UserResponseSelfCache.model_validate(cached)
            return UserResponseSelf.model_validate(raw.model_dump())

        user = await UserRepositoryBase.get_user_by_id(
            session,
            current_user.id,
            excluded_roles=frozenset({UserRole.STUDENT}),
        )
        ensure_exists(user, UserNotFoundError(HTTP404.USER))

        raw = UserResponseSelfCache.model_validate(user)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return UserResponseSelf.model_validate(user)

    @staticmethod
    async def update_me_credentials(
        session: AsyncSession,
        current_user_id: int,
        update_request: UpdateUserCredentials,
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            session, current_user_id, load_session=True
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        user_with_session = target_user.session

        username_changing = (
            update_request.username is not None
            and update_request.username != target_user.username
        )
        email_requested = (
            update_request.email is not None
            and update_request.email != target_user.email
        )

        if not username_changing and not email_requested:
            raise NoChangesDetectedError(HTTP400.NO_CHANGES_DETECTED)

        if email_requested:
            pending_still_active = (
                user_with_session.email_change_code_expires_at is not None
                and user_with_session.email_change_code_expires_at > datetime.now(UTC)
            )

            if (
                user_with_session.pending_new_email == update_request.email
                and pending_still_active
            ):
                logger.warning(
                    "email_change_request_denied",
                    target_user_id=current_user_id,
                    denial_reason="duplicate_pending_request",
                )

                raise DuplicateEmailChangeRequestError(
                    "An identical email change request is already pending"
                )

        try:
            if username_changing:
                target_user.username = update_request.username
                target_user.session.access_token_version += 1

            if email_requested:
                raw_code, hashed_code = generate_email_change_code()
                code_expires_at = datetime.now(UTC) + timedelta(
                    minutes=settings.EMAIL_CHANGE_CODE_EXPIRES_MINUTES
                )

                user_with_session.pending_new_email = update_request.email
                user_with_session.email_change_code_hash = hashed_code
                user_with_session.email_change_code_expires_at = code_expires_at

            await session.commit()
            await session.refresh(target_user)

            if email_requested:
                asyncio.create_task(
                    email_sender.send_safe(
                        email_sender.send_email_change_verification(
                            update_request.email, raw_code
                        ),
                        email_type=EmailType.EMAIL_CHANGE_CODE,
                    )
                )

            await delete_cache(
                UserCacheKey.user_detail_key_admin(target_user.id),
                UserCacheKey.user_detail_key_staff(target_user.id),
                UserCacheKey.user_detail_key_self(target_user.id),
            )

            if username_changing:
                await delete_cache(
                    SessionCacheKey.access_token_version_key(target_user.id)
                )

                logger.info(
                    "username_updated",
                    target_user_id=current_user_id,
                    new_username=target_user.username,
                    method="self_service",
                )

            if email_requested:
                logger.info(
                    "user_email_update_requested",
                    target_user_id=current_user_id,
                    email_change_requested=target_user.email,
                    method="self_service",
                )

        except IntegrityError as exc:
            await session.rollback()

            logger.error(
                "user_credentials_update_failed",
                target_user_id=current_user_id,
                reason=str(exc.orig),
                method="self_service",
            )

            handle_username_integrity_error(exc)
            raise_unhandled_integrity_error(exc)

    @staticmethod
    async def confirm_email_change(
        session: AsyncSession,
        current_user_id: int,
        confirm_request: ConfirmEmailChange,
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            session, current_user_id, load_session=True
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        user_with_session = target_user.session
        if (
            user_with_session.pending_new_email is None
            or user_with_session.email_change_code_hash is None
        ):
            raise NoPendingEmailChangeError("No email change is currently pending")

        if user_with_session.email_change_code_expires_at < datetime.now(UTC):
            raise EmailChangeCodeExpiredError("Email change code has expired")

        if not verify_email_change_code(
            confirm_request.code, user_with_session.email_change_code_hash
        ):
            logger.warning(
                "email_change_confirmation_denied",
                target_user_id=current_user_id,
                denial_reason="invalid_code",
            )

            raise InvalidEmailChangeCodeError("Invalid email change code")

        new_email = user_with_session.pending_new_email
        is_student = target_user.role == UserRole.STUDENT

        if is_student:
            await acquire_student_contact_lock(
                session, phone_number=None, email=new_email
            )

            await check_contact_limit(
                session,
                current_user_id,
                target_username=target_user.username,
                phone_number=None,
                email=new_email,
                role=UserRole.STUDENT,
                resolved_role=UserRole.STUDENT,
                max_allowed=STUDENT_MAX_SHARED_CONTACT,
                exclude_user_id=current_user_id,
            )

        try:
            old_email = target_user.email
            target_user.email = new_email

            user_with_session.pending_new_email = None
            user_with_session.email_change_code_hash = None
            user_with_session.email_change_code_expires_at = None

            user_with_session.access_token_version += 1
            user_with_session.refresh_token_hash = None
            user_with_session.refresh_token_family = None
            user_with_session.refresh_token_expires_at = None

            await session.commit()
            await session.refresh(target_user)

            asyncio.create_task(
                email_sender.send_safe(
                    email_sender.send_email_changed_notification(
                        target_user.email, old_email, target_user.email
                    ),
                    email_type=EmailType.EMAIL_CHANGED,
                )
            )

            await delete_cache(
                SessionCacheKey.access_token_version_key(current_user_id),
                UserCacheKey.user_detail_key_admin(current_user_id),
                UserCacheKey.user_detail_key_staff(current_user_id),
                UserCacheKey.user_detail_key_self(current_user_id),
            )

            logger.info(
                "email_changed",
                target_user_id=current_user_id,
                method="self_service",
            )

        except IntegrityError as exc:
            await session.rollback()

            logger.error(
                "email_change_confirmation_failed",
                target_user_id=current_user_id,
                reason=str(exc.orig),
                method="self_service",
            )

            if not is_student:
                handle_non_student_unique_contact_error(exc)
            raise_unhandled_integrity_error(exc)

    @staticmethod
    async def update_me_password(
        session: AsyncSession,
        current_user_id: int,
        update_request: UpdateMePassword,
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            session, current_user_id, load_session=True
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        is_current_password_valid = await verify_password(
            update_request.current_password, target_user.password_hash
        )
        if not is_current_password_valid:
            logger.warning(
                "password_change_denied",
                target_user_id=current_user_id,
                denial_reason="incorrect_current_password",
                method="self_service",
            )

            raise IncorrectPasswordError("Current password is incorrect")

        new_password_hash = await hash_password(update_request.new_password)

        target_user.password_hash = new_password_hash

        target_user.session.access_token_version += 1
        target_user.session.refresh_token_hash = None
        target_user.session.refresh_token_family = None
        target_user.session.refresh_token_expires_at = None

        await session.commit()

        asyncio.create_task(
            email_sender.send_safe(
                email_sender.send_password_changed_notification(target_user.email),
                email_type=EmailType.PASSWORD_CHANGED,
            )
        )

        await delete_cache(SessionCacheKey.access_token_version_key(current_user_id))

        logger.info(
            "password_changed",
            target_user_id=current_user_id,
            method="self_service",
        )

    @staticmethod
    async def get_my_student_profile(
        session: AsyncSession, current_user: CurrentUser
    ) -> StudentResponseSelf:
        cache_key = UserCacheKey.user_detail_key_self(current_user.id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = StudentResponseSelfCache.model_validate(cached)
            return StudentResponseSelf.model_validate(raw.model_dump())

        student = await UserRepositoryBase.get_user_by_id(
            session,
            current_user.id,
            allowed_roles=frozenset({UserRole.STUDENT}),
            load_group=True,
        )
        ensure_exists(student, UserNotFoundError(HTTP404.USER))

        raw = StudentResponseSelfCache.model_validate(student)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return StudentResponseSelf.model_validate(student)
