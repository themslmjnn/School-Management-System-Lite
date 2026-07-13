import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.advisory_locks import acquire_student_contact_lock
from src.core.caching import delete_cache
from src.core.config import settings
from src.core.logging import get_logger
from src.core.security import (
    generate_email_change_code,
    hash_password,
    verify_email_change_code,
    verify_password,
)
from src.users.models.users import User
from src.users.repositories.users import UserRepositoryBase
from src.users.schemas.users import (
    ConfirmEmailChange,
    UpdateMeCredentials,
    UpdateMePassword,
    UpdateMeProfile,
)
from src.users.services.system_admin import check_contact_limit
from src.utils import email as email_sender
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.constants import HTTP404
from src.utils.enums import EmailType, UserRole
from src.utils.exceptions import (
    EmailChangeCodeExpiredError,
    IncorrectPasswordError,
    InvalidEmailChangeCodeError,
    NoPendingEmailChangeError,
    ProfileFieldsNotEditableForRoleError,
    UserNotFoundError,
    handle_non_student_unique_contact_error,
    handle_username_integrity_error,
    raise_unhandled_integrity_error,
)
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)

PROFILE_EDITABLE_ROLES = frozenset({UserRole.SYSTEM_ADMIN, UserRole.GUARDIAN})
STUDENT_MAX_SHARED_CONTACT = 3


class UserServiceSelf:
    @staticmethod
    async def update_me_profile(
        db: AsyncSession,
        current_user_id: int,
        update_request: UpdateMeProfile,
    ) -> User:
        current_user = await UserRepositoryBase.get_user_by_id(db, current_user_id)
        ensure_exists(current_user, UserNotFoundError(HTTP404.USER))

        if current_user.role not in PROFILE_EDITABLE_ROLES:
            logger.warning(
                "profile_update_denied",
                target_user_id=current_user_id,
                target_role=current_user.role.value,
                denial_reason="role_not_permitted_to_edit_profile_fields",
            )
            raise ProfileFieldsNotEditableForRoleError(
                "Your role does not permit editing profile fields directly. "
                "Contact a system administrator for changes."
            )

        try:
            update_object(current_user, update_request)

            await db.commit()
            await db.refresh(current_user)

            asyncio.create_task(
                email_sender.send_safe(
                    email_sender.send_account_info_updated_email(current_user.email),
                    email_type=EmailType.UPDATING_ACCOUNT,
                )
            )

            await delete_cache(UserCacheKey.user_detail_key_self(current_user_id))

            logger.info(
                "user_profile_updated",
                target_user_id=current_user_id,
                method="self_update",
            )

            return current_user

        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "profile_update_failed",
                target_user_id=current_user_id,
                reason=str(e.orig),
            )
            handle_non_student_unique_contact_error(e)
            raise_unhandled_integrity_error(e)

    @staticmethod
    async def update_me_credentials(
        db: AsyncSession,
        current_user_id: int,
        update_request: UpdateMeCredentials,
    ) -> None:
        current_user = await UserRepositoryBase.get_user_by_id(
            db, current_user_id, load_session=True
        )
        ensure_exists(current_user, UserNotFoundError(HTTP404.USER))

        email_requested = (
            update_request.email is not None
            and update_request.email != current_user.email
        )

        try:
            if update_request.username is not None:
                current_user.username = update_request.username

            raw_code = None
            if email_requested:
                raw_code, hashed_code = generate_email_change_code()
                code_expires_at = datetime.now(UTC) + timedelta(
                    minutes=settings.EMAIL_CHANGE_CODE_EXPIRES_MINUTES
                )

                current_user.session.pending_new_email = update_request.email
                current_user.session.email_change_code_hash = hashed_code
                current_user.session.email_change_code_expires_at = code_expires_at

            await db.commit()

            if email_requested:
                asyncio.create_task(
                    email_sender.send_safe(
                        email_sender.send_email_change_code_email(
                            update_request.email, raw_code
                        ),
                        email_type=EmailType.EMAIL_CHANGE_CODE,
                    )
                )

            await delete_cache(UserCacheKey.user_detail_key_self(current_user_id))

            logger.info(
                "user_credentials_update_requested",
                target_user_id=current_user_id,
                username_changed=update_request.username is not None,
                email_change_requested=email_requested,
            )

        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "user_credentials_update_failed",
                target_user_id=current_user_id,
                reason=str(e.orig),
            )

            handle_username_integrity_error(e)
            raise_unhandled_integrity_error(e)

    @staticmethod
    async def confirm_email_change(
        db: AsyncSession,
        current_user_id: int,
        confirm_request: ConfirmEmailChange,
    ) -> None:
        current_user = await UserRepositoryBase.get_user_by_id(
            db, current_user_id, load_session=True
        )
        ensure_exists(current_user, UserNotFoundError(HTTP404.USER))

        session = current_user.session
        if session.pending_new_email is None or session.email_change_code_hash is None:
            raise NoPendingEmailChangeError("No email change is currently pending")

        if session.email_change_code_expires_at < datetime.now(UTC):
            raise EmailChangeCodeExpiredError("Email change code has expired")

        if not verify_email_change_code(
            confirm_request.code, session.email_change_code_hash
        ):
            logger.warning(
                "email_change_confirmation_denied",
                target_user_id=current_user_id,
                denial_reason="invalid_code",
            )
            raise InvalidEmailChangeCodeError("Invalid email change code")

        new_email = session.pending_new_email
        is_student = current_user.role == UserRole.STUDENT

        if is_student:
            await acquire_student_contact_lock(db, phone_number=None, email=new_email)
            await check_contact_limit(
                db,
                current_user_id,
                target_username=current_user.username,
                phone_number=None,
                email=new_email,
                role=UserRole.STUDENT,
                resolved_role=UserRole.STUDENT,
                max_allowed=STUDENT_MAX_SHARED_CONTACT,
                exclude_user_id=current_user_id,
            )

        try:
            old_email = current_user.email
            current_user.email = new_email

            session.pending_new_email = None
            session.email_change_code_hash = None
            session.email_change_code_expires_at = None

            await db.commit()

            asyncio.create_task(
                email_sender.send_safe(
                    email_sender.send_email_changed_notification(old_email),
                    email_type=EmailType.EMAIL_CHANGED,
                )
            )

            await delete_cache(UserCacheKey.user_detail_key_self(current_user_id))

            logger.info("user_email_changed", target_user_id=current_user_id)

        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "email_change_confirmation_failed",
                target_user_id=current_user_id,
                reason=str(e.orig),
            )
            if not is_student:
                handle_non_student_unique_contact_error(e)
            raise_unhandled_integrity_error(e)

    @staticmethod
    async def update_me_password(
        db: AsyncSession,
        current_user_id: int,
        update_request: UpdateMePassword,
    ) -> None:
        current_user = await UserRepositoryBase.get_user_by_id(
            db, current_user_id, load_session=True
        )
        ensure_exists(current_user, UserNotFoundError(HTTP404.USER))

        is_current_password_valid = await verify_password(
            update_request.current_password, current_user.password_hash
        )
        if not is_current_password_valid:
            logger.warning(
                "password_change_denied",
                target_user_id=current_user_id,
                denial_reason="incorrect_current_password",
            )
            raise IncorrectPasswordError("Current password is incorrect")

        new_password_hash = await hash_password(update_request.new_password)

        current_user.password_hash = new_password_hash
        current_user.session.access_token_version += 1
        current_user.session.refresh_token_hash = None
        current_user.session.refresh_token_family = None
        current_user.session.refresh_token_expires_at = None

        await db.commit()

        asyncio.create_task(
            email_sender.send_safe(
                email_sender.send_password_changed_notification(current_user.email),
                email_type=EmailType.PASSWORD_CHANGED,
            )
        )

        await delete_cache(
            UserCacheKey.user_detail_key_self(current_user_id),
            SessionCacheKey.access_token_version_key(current_user_id),
        )

        logger.info(
            "user_password_changed",
            target_user_id=current_user_id,
        )
