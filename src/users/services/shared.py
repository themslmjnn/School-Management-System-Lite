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
from src.users.exceptions.constants import HTTP404
from src.users.exceptions.exceptions import (
    DuplicateEmailChangeRequestError,
    EmailChangeCodeExpiredError,
    IncorrectPasswordError,
    InvalidEmailChangeCodeError,
    NoPendingEmailChangeError,
    ProfileFieldsNotEditableForRoleError,
    UserNotFoundError,
    handle_non_student_unique_contact_error,
    handle_username_integrity_error,
)
from src.users.models.user import User
from src.users.repositories.guardian_link import GuardianLinkRepositoryShared
from src.users.repositories.user import UserRepositoryBase
from src.users.schemas.guardian_link import ChildResponse
from src.users.schemas.user import (
    ConfirmEmailChange,
    UpdateMeCredentials,
    UpdateMePassword,
    UpdateMeProfile,
)
from src.users.services.system_admin.user import check_contact_limit
from src.utils import email as email_sender
from src.utils.base_constant import HTTP400
from src.utils.base_exception import (
    NoChangesDetectedError,
    raise_unhandled_integrity_error,
)
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.enums import EmailType, UserRole
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
        target_user = await UserRepositoryBase.get_user_by_id(
            db, current_user_id, load_session=True
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        session = target_user.session

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
                session.email_change_code_expires_at is not None
                and session.email_change_code_expires_at > datetime.now(UTC)
            )
            if (
                session.pending_new_email == update_request.email
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
                session.pending_new_email = update_request.email
                session.email_change_code_hash = hashed_code
                session.email_change_code_expires_at = code_expires_at

            await db.commit()

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
                UserCacheKey.user_detail_key_self(target_user.id),
                UserCacheKey.user_detail_key_admin(target_user.id),
                UserCacheKey.user_detail_key_staff(target_user.id),
            )

            if username_changing:
                await delete_cache(
                    SessionCacheKey.access_token_version_key(target_user.id)
                )

            logger.info(
                "user_credentials_update_requested",
                target_user_id=current_user_id,
                username_changed=username_changing,
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
        target_user = await UserRepositoryBase.get_user_by_id(
            db, current_user_id, load_session=True
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        session = target_user.session
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
        is_student = target_user.role == UserRole.STUDENT

        if is_student:
            await acquire_student_contact_lock(db, phone_number=None, email=new_email)
            await check_contact_limit(
                db,
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

            session.pending_new_email = None
            session.email_change_code_hash = None
            session.email_change_code_expires_at = None

            session.access_token_version += 1
            session.refresh_token_hash = None
            session.refresh_token_family = None
            session.refresh_token_expires_at = None

            await db.commit()
            await db.refresh(target_user)

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
                "user_email_changed",
                target_user_id=current_user_id,
            )

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
        target_user = await UserRepositoryBase.get_user_by_id(
            db, current_user_id, load_session=True
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
            )

            raise IncorrectPasswordError("Current password is incorrect")

        new_password_hash = await hash_password(update_request.new_password)

        target_user.password_hash = new_password_hash

        target_user.session.access_token_version += 1
        target_user.session.refresh_token_hash = None
        target_user.session.refresh_token_family = None
        target_user.session.refresh_token_expires_at = None

        await db.commit()

        asyncio.create_task(
            email_sender.send_safe(
                email_sender.send_password_changed_notification(target_user.email),
                email_type=EmailType.PASSWORD_CHANGED,
            )
        )

        await delete_cache(SessionCacheKey.access_token_version_key(current_user_id))

        logger.info(
            "user_password_changed",
            target_user_id=current_user_id,
        )


class GuardianLinkServiceShared:
    @staticmethod
    async def get_children_for_guardian(
        db: AsyncSession, guardian_id: int
    ) -> list[ChildResponse]:
        links = await GuardianLinkRepositoryShared.get_children_for_guardian(
            db, guardian_id
        )

        return [
            ChildResponse(
                id=link.student.id,
                firstname=link.student.firstname,
                lastname=link.student.lastname,
                middlename=link.student.middlename,
                priority=link.priority,
            )
            for link in links
        ]
