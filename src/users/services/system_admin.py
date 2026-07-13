import asyncio
from datetime import UTC, datetime, timedelta
from typing import assert_never

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.advisory_locks import acquire_student_contact_lock
from src.core.caching import delete_cache
from src.core.config import settings
from src.core.logging import get_logger
from src.core.security import generate_invite_token
from src.emails.repository import PendingEmailRepository
from src.users.models.users import User, UserActivation, UserLoginLockout, UserSession
from src.users.repositories.users import (
    UserRepositoryBase,
)
from src.users.schemas.users import (
    CreateGuardianAdmin,
    CreateRequest,
    CreateStaffAdmin,
    CreateStudentAdmin,
    UpdateUser,
    UpdateUserCredentials,
)
from src.utils import email as email_sender
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.constants import HTTP404
from src.utils.enums import EmailType, UserRole, UserStatus
from src.utils.exceptions import (
    CannotCreateDirectorError,
    CannotCreateSystemAdminError,
    MaxStaffOrGuardianPerEmailError,
    MaxStaffOrGuardianPerPhoneNumberError,
    MaxStudentsPerEmailError,
    MaxStudentsPerPhoneNumberError,
    UserNotFoundError,
    handle_non_student_unique_contact_error,
    handle_username_integrity_error,
    raise_unhandled_integrity_error,
)
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)

STUDENT_MAX_SHARED_CONTACT = 3
STAFF_AND_GUARDIAN_MAX_SHARED_CONTACT = 1
BLOCKED_ROLES_VIA_API = frozenset(
    {
        UserRole.SYSTEM_ADMIN,
        UserRole.DIRECTOR,
    }
)
SYSTEM_ADMIN_INVISIBLE_ROLES = frozenset({UserRole.SYSTEM_ADMIN})


async def _check_contact_limit(
    db: AsyncSession,
    current_user_id: int,
    *,
    target_username: str,
    phone_number: str | None,
    email: str | None,
    role: UserRole | None,
    resolved_role: UserRole,
    max_allowed: int,
    exclude_user_id: int | None = None,
) -> None:
    is_student = role == UserRole.STUDENT

    if phone_number is not None:
        phone_count = await UserRepositoryBase.count_users_with_contact(
            db,
            role,
            phone_number=phone_number,
            email=None,
            exclude_user_id=exclude_user_id,
        )
        if phone_count >= max_allowed:
            logger.warning(
                "user_registration_denied",
                actor_user_id=current_user_id,
                target_username=target_username,
                requested_role=resolved_role,
                denial_reason="maximum_number_of_identical_phone_numbers_reached",
            )
            if is_student:
                raise MaxStudentsPerPhoneNumberError(
                    "Maximum number of students with this phone number reached"
                )
            raise MaxStaffOrGuardianPerPhoneNumberError(
                "Maximum number of staff or guardians with this phone number reached"
            )

    if email is not None:
        email_count = await UserRepositoryBase.count_users_with_contact(
            db,
            role,
            phone_number=None,
            email=email,
            exclude_user_id=exclude_user_id,
        )
        if email_count >= max_allowed:
            logger.warning(
                "user_registration_denied",
                actor_user_id=current_user_id,
                target_username=target_username,
                requested_role=resolved_role,
                denial_reason="maximum_number_of_identical_emails_reached",
            )
            if is_student:
                raise MaxStudentsPerEmailError(
                    "Maximum number of students with this email reached"
                )
            raise MaxStaffOrGuardianPerEmailError(
                "Maximum number of staff or guardians with this email reached"
            )


# COMPLETED!!!
class UserServiceAdmin:
    @staticmethod
    async def register_user(
        db: AsyncSession,
        current_user_id: int,
        create_request: CreateRequest,
    ) -> User:
        match create_request:
            case CreateStaffAdmin():
                if create_request.role in BLOCKED_ROLES_VIA_API:
                    denial_reason = {
                        UserRole.SYSTEM_ADMIN: "system_admin_creation_via_api_is_forbidden",
                        UserRole.DIRECTOR: "director_creation_via_api_is_forbidden",
                    }[create_request.role]

                    exception_map = {
                        UserRole.SYSTEM_ADMIN: CannotCreateSystemAdminError,
                        UserRole.DIRECTOR: CannotCreateDirectorError,
                    }

                    logger.warning(
                        "user_registration_denied",
                        actor_user_id=current_user_id,
                        target_username=create_request.username,
                        requested_role=create_request.role.value,
                        denial_reason=denial_reason,
                    )

                    raise exception_map[create_request.role](
                        denial_reason.replace("_", " ").capitalize()
                    )

                resolved_role = create_request.role
                contact_limit_role = None
                max_allowed = STAFF_AND_GUARDIAN_MAX_SHARED_CONTACT

            case CreateGuardianAdmin():
                resolved_role = UserRole.GUARDIAN
                contact_limit_role = None
                max_allowed = STAFF_AND_GUARDIAN_MAX_SHARED_CONTACT

            case CreateStudentAdmin():
                resolved_role = UserRole.STUDENT
                contact_limit_role = UserRole.STUDENT
                max_allowed = STUDENT_MAX_SHARED_CONTACT

            case _:
                assert_never(create_request)

        is_student = resolved_role == UserRole.STUDENT

        if is_student:
            await acquire_student_contact_lock(
                db,
                phone_number=create_request.phone_number,
                email=create_request.email,
            )

        await _check_contact_limit(
            db,
            current_user_id,
            target_username=create_request.username,
            phone_number=create_request.phone_number,
            email=create_request.email,
            role=contact_limit_role,
            resolved_role=resolved_role,
            max_allowed=max_allowed,
        )

        raw_invite_token, hashed_invite_token = generate_invite_token()
        invite_token_expires_at = datetime.now(UTC) + timedelta(
            hours=settings.INVITE_TOKEN_EXPIRES_HOURS
        )

        try:
            new_user = User(
                username=create_request.username,
                firstname=create_request.firstname.capitalize(),
                lastname=create_request.lastname.capitalize(),
                middlename=create_request.middlename.capitalize()
                if create_request.middlename
                else None,
                phone_number=create_request.phone_number,
                email=create_request.email,
                role=resolved_role,
                status=UserStatus.PENDING_ACTIVATION,
                is_active=False,
                created_by=current_user_id,
                date_of_birth=create_request.date_of_birth if is_student else None,
                address=create_request.address if is_student else None,
            )

            UserRepositoryBase.add_entity(db, user=new_user)
            await db.flush()

            new_user_activation = UserActivation(
                user_id=new_user.id,
                invite_token_hash=hashed_invite_token,
                invite_token_expires_at=invite_token_expires_at,
            )
            new_user_session = UserSession(user_id=new_user.id)
            new_user_login_lockout = UserLoginLockout(user_id=new_user.id)

            UserRepositoryBase.add_entity(
                db,
                user_activation=new_user_activation,
                user_session=new_user_session,
                user_login_lockout=new_user_login_lockout,
            )

            subject, html_body, text_body = email_sender.build_invite_email(
                raw_invite_token, new_user.username
            )

            PendingEmailRepository.add_pending_email(
                db,
                recipient=new_user.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                email_type=EmailType.INVITE,
                triggered_by=current_user_id,
                recipient_user_id=new_user.id,
            )

            await db.commit()
            await db.refresh(new_user)

            logger.info(
                "user_registered",
                new_user_id=new_user.id,
                target_username=create_request.username,
                role=resolved_role,
                created_by=current_user_id,
            )

            return new_user

        except IntegrityError as e:
            await db.rollback()

            logger.warning(
                "user_registration_failed",
                reason="integrity_error",
                error=str(e.orig),
                requested_by=current_user_id,
            )

            handle_username_integrity_error(e)
            if not is_student:
                handle_non_student_unique_contact_error(e)
            raise_unhandled_integrity_error(e)

    @staticmethod
    async def update_user(
        db: AsyncSession,
        current_user_id: int,
        target_user_id: int,
        update_request: UpdateUser,
    ) -> User:
        target_user = await UserRepositoryBase.get_user_by_id(
            db, target_user_id, excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        is_student = target_user.role == UserRole.STUDENT
        phone_number_changing = (
            update_request.phone_number is not None
            and update_request.phone_number != target_user.phone_number
        )

        if is_student and phone_number_changing:
            await acquire_student_contact_lock(
                db, phone_number=update_request.phone_number, email=None
            )
            await _check_contact_limit(
                db,
                current_user_id,
                target_username=target_user.username,
                phone_number=update_request.phone_number,
                email=None,
                role=UserRole.STUDENT,
                resolved_role=UserRole.STUDENT,
                max_allowed=STUDENT_MAX_SHARED_CONTACT,
                exclude_user_id=target_user_id,
            )

        try:
            update_object(target_user, update_request)

            await db.commit()
            await db.refresh(target_user)

            asyncio.create_task(
                email_sender.send_safe(
                    email_sender.send_account_info_updated_email(target_user.email),
                    email_type="updating_account",
                )
            )

            await delete_cache(
                UserCacheKey.user_detail_key_admin(target_user_id),
                UserCacheKey.user_detail_key_staff(target_user_id),
                UserCacheKey.user_detail_key_self(target_user_id),
            )

            logger.info(
                "user_updated",
                target_user_id=target_user_id,
                updated_by=current_user_id,
                method="admin_update",
            )

            return target_user
        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "update_user_denied",
                target_user_id=target_user_id,
                requested_by=current_user_id,
                reason=str(e.orig),
            )

            if not is_student:
                handle_non_student_unique_contact_error(e)
            raise_unhandled_integrity_error(e)

    @staticmethod
    async def update_user_credentials(
        db: AsyncSession,
        current_user_id: int,
        target_user_id: int,
        update_request: UpdateUserCredentials,
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            db,
            target_user_id,
            excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES,
            load_session=True,
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        is_student = target_user.role == UserRole.STUDENT
        email_changing = (
            update_request.email is not None
            and update_request.email != target_user.email
        )

        if is_student and email_changing:
            await acquire_student_contact_lock(
                db, phone_number=None, email=update_request.email
            )
            await _check_contact_limit(
                db,
                current_user_id,
                target_username=target_user.username,
                phone_number=None,
                email=update_request.email,
                role=UserRole.STUDENT,
                resolved_role=UserRole.STUDENT,
                max_allowed=STUDENT_MAX_SHARED_CONTACT,
                exclude_user_id=target_user_id,
            )

        try:
            old_email = target_user.email
            update_object(target_user, update_request)

            target_user.session.access_token_version += 1
            target_user.session.refresh_token_hash = None
            target_user.session.refresh_token_family = None
            target_user.session.refresh_token_expires_at = None
            target_user.session.pending_new_email = None
            target_user.session.email_change_code_hash = None
            target_user.session.email_change_code_expires_at = None

            await db.commit()

            asyncio.create_task(
                email_sender.send_safe(
                    email_sender.send_admin_credentials_override_notification(
                        old_email
                    ),
                    email_type=EmailType.ADMIN_CREDENTIALS_OVERRIDE,
                )
            )

            await delete_cache(
                UserCacheKey.user_detail_key_admin(target_user_id),
                UserCacheKey.user_detail_key_staff(target_user_id),
                UserCacheKey.user_detail_key_self(target_user_id),
                SessionCacheKey.access_token_version_key(target_user_id),
            )

            logger.info(
                "admin_email_override",
                target_user_id=target_user_id,
                updated_by=current_user_id,
            )

        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "admin_email_override_failed",
                target_user_id=target_user_id,
                requested_by=current_user_id,
                reason=str(e.orig),
            )

            handle_username_integrity_error(e)
            if not is_student:
                handle_non_student_unique_contact_error(e)
            raise_unhandled_integrity_error(e)
