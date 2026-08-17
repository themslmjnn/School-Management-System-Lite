import asyncio
from datetime import UTC, datetime, timedelta
from typing import assert_never

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.advisory_locks import acquire_student_contact_lock
from src.core.caching import delete_cache, get_cache, set_cache
from src.core.config import settings
from src.core.dependencies import CurrentUser
from src.core.logging import get_logger
from src.core.pagination import PaginatedResponse
from src.core.security import generate_invite_token, generate_reset_password_token
from src.emails.repository import PendingEmailRepository
from src.users.models.activation import UserActivation
from src.users.models.login_lockout import UserLoginLockout
from src.users.models.session import UserSession
from src.users.models.user import User
from src.users.repositories.user import (
    UserRepositoryAdmin,
    UserRepositoryBase,
)
from src.users.schemas.shared import StudentCacheSchema, StudentResponseAdminDetailed
from src.users.schemas.system_admin import (
    CreateStudentAdmin,
    CreateTeacherAdmin,
    CreateUserRequest,
    SearchUserAdmin,
    UpdateStudentAdmin,
    UpdateUser,
    UpdateUserCredentials,
    UserCacheSchema,
    UserResponseAdminDetailed,
)
from src.users.utils.check_contact_limit import check_contact_limit
from src.users.utils.constants import HTTP404
from src.users.utils.exceptions import (
    UserAlreadyActiveError,
    UserAlreadyInactiveError,
    UserNotFoundError,
    UserTypeMismatchError,
    handle_non_student_unique_contact_error,
    handle_username_integrity_error,
)
from src.utils import email as email_sender
from src.utils.base_exception import raise_unhandled_integrity_error
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.enums import EmailType, UserRole, UserStatus
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)

STUDENT_MAX_SHARED_CONTACT = 3
TEACHER_MAX_SHARED_CONTACT = 1
STAFF_ROLES = frozenset({UserRole.TEACHER})
SYSTEM_ADMIN_INVISIBLE_ROLES = frozenset({UserRole.SYSTEM_ADMIN})


class UserServiceAdmin:
    @staticmethod
    async def register_user(
        session: AsyncSession,
        current_user_id: int,
        create_request: CreateUserRequest,
    ) -> User:
        match create_request:
            case CreateTeacherAdmin():
                resolved_role = UserRole.TEACHER
                contact_limit_role = None
                max_allowed = TEACHER_MAX_SHARED_CONTACT

            case CreateStudentAdmin():
                resolved_role = UserRole.STUDENT
                contact_limit_role = UserRole.STUDENT
                max_allowed = STUDENT_MAX_SHARED_CONTACT

            case _:
                assert_never(create_request)

        is_student = resolved_role == UserRole.STUDENT

        if is_student:
            await acquire_student_contact_lock(
                session,
                phone_number=create_request.phone_number,
                email=create_request.email,
            )

        await check_contact_limit(
            session,
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
                firstname=create_request.firstname,
                lastname=create_request.lastname,
                middlename=create_request.middlename,
                phone_number=create_request.phone_number,
                email=create_request.email,
                role=resolved_role,
                status=UserStatus.PENDING_ACTIVATION,
                is_active=False,
                created_by=current_user_id,
                date_of_birth=create_request.date_of_birth if is_student else None,
                address=create_request.address if is_student else None,
            )

            session.add(new_user)
            await session.flush()

            new_user_activation = UserActivation(
                user_id=new_user.id,
                invite_token_hash=hashed_invite_token,
                invite_token_expires_at=invite_token_expires_at,
            )
            new_user_session = UserSession(user_id=new_user.id)
            new_user_login_lockout = UserLoginLockout(user_id=new_user.id)

            session.add(new_user_activation)
            session.add(new_user_session)
            session.add(new_user_login_lockout)

            subject, html_body, text_body = email_sender.build_invite_email(
                raw_invite_token, new_user.username
            )

            PendingEmailRepository.add_pending_email(
                session,
                recipient=new_user.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                email_type=EmailType.INVITE,
                triggered_by=current_user_id,
                recipient_user_id=new_user.id,
            )

            await session.commit()
            await session.refresh(new_user)

            logger.info(
                "user_registered",
                new_user_id=new_user.id,
                target_username=create_request.username,
                role=resolved_role,
                created_by=current_user_id,
            )

            return new_user

        except IntegrityError as e:
            await session.rollback()

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
        session: AsyncSession,
        current_user_id: int,
        target_user_id: int,
        update_request: UpdateUser,
    ) -> User:
        target_user = await UserRepositoryBase.get_user_by_id(
            session, target_user_id, excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        is_student = target_user.role == UserRole.STUDENT
        request_is_student_shaped = isinstance(update_request, UpdateStudentAdmin)

        if is_student != request_is_student_shaped:
            logger.warning(
                "update_user_type_mismatch",
                actor_user_id=current_user_id,
                target_user_id=target_user_id,
                target_user_role=target_user.role.value,
                submitted_type=update_request.type,
            )

            raise UserTypeMismatchError(
                "Submitted update payload type does not match the target user's role"
            )

        phone_number_changing = (
            update_request.phone_number is not None
            and update_request.phone_number != target_user.phone_number
        )

        if is_student and phone_number_changing:
            await acquire_student_contact_lock(
                session, phone_number=update_request.phone_number, email=None
            )
            await check_contact_limit(
                session,
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

            await session.commit()
            await session.refresh(target_user)

            asyncio.create_task(
                email_sender.send_safe(
                    email_sender.send_account_info_updated_email(target_user.email),
                    email_type=EmailType.UPDATING_ACCOUNT,
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

        except IntegrityError as e:
            await session.rollback()

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
        session: AsyncSession,
        current_user_id: int,
        target_user_id: int,
        update_request: UpdateUserCredentials,
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            session,
            target_user_id,
            excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES,
            load_session=True,
            load_activation=True,
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        is_student = target_user.role == UserRole.STUDENT
        email_changing = (
            update_request.email is not None
            and update_request.email != target_user.email
        )
        should_reissue_activation_token = (
            email_changing and target_user.status == UserStatus.PENDING_ACTIVATION
        )

        if is_student and email_changing:
            await acquire_student_contact_lock(
                session, phone_number=None, email=update_request.email
            )
            await check_contact_limit(
                session,
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
            old_username = target_user.username

            update_object(target_user, update_request)

            target_user.session.access_token_version += 1
            target_user.session.refresh_token_hash = None
            target_user.session.refresh_token_family = None
            target_user.session.refresh_token_expires_at = None
            target_user.session.pending_new_email = None
            target_user.session.email_change_code_hash = None
            target_user.session.email_change_code_expires_at = None

            if should_reissue_activation_token:
                raw_invite_token, hashed_invite_token = generate_invite_token()
                invite_token_expires_at = datetime.now(UTC) + timedelta(
                    hours=settings.INVITE_TOKEN_EXPIRES_HOURS
                )

                target_user.activation.invite_token_hash = hashed_invite_token
                target_user.activation.invite_token_expires_at = invite_token_expires_at

                subject, html_body, text_body = email_sender.build_invite_email(
                    raw_invite_token, target_user.username
                )

                PendingEmailRepository.add_pending_email(
                    session,
                    recipient=target_user.email,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                    email_type=EmailType.INVITE,
                    triggered_by=current_user_id,
                    recipient_user_id=target_user.id,
                )

            username_changed = old_username != target_user.username
            email_changed = old_email != target_user.email

            if not should_reissue_activation_token:
                notify_old_username = old_username if username_changed else None
                notify_new_username = target_user.username if username_changed else None
                notify_old_email = old_email if email_changed else None
                notify_new_email = target_user.email if email_changed else None

                subject, html_body, text_body = (
                    email_sender.build_admin_credentials_override_notification_email(
                        notify_old_username,
                        notify_new_username,
                        notify_old_email,
                        notify_new_email,
                    )
                )

                PendingEmailRepository.add_pending_email(
                    session,
                    recipient=old_email,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                    email_type=EmailType.ADMIN_CREDENTIALS_OVERRIDE,
                    triggered_by=current_user_id,
                    recipient_user_id=target_user.id,
                )

            await session.commit()

            await delete_cache(
                SessionCacheKey.access_token_version_key(target_user_id),
                UserCacheKey.user_detail_key_admin(target_user_id),
                UserCacheKey.user_detail_key_staff(target_user_id),
                UserCacheKey.user_detail_key_self(target_user_id),
            )

            logger.info(
                "admin_credentials_override",
                target_user_id=target_user_id,
                updated_by=current_user_id,
            )

        except IntegrityError as e:
            await session.rollback()

            logger.error(
                "admin_credentials_override_failed",
                target_user_id=target_user_id,
                requested_by=current_user_id,
                reason=str(e.orig),
            )

            handle_username_integrity_error(e)
            if not is_student:
                handle_non_student_unique_contact_error(e)
            raise_unhandled_integrity_error(e)

    @staticmethod
    async def deactivate_user(
        session: AsyncSession, current_user_id: int, target_user_id: int
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            session,
            target_user_id,
            load_session=True,
            excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES,
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        if not target_user.is_active:
            logger.warning(
                "deactivate_user_failed",
                target_user_id=target_user_id,
                requested_by=current_user_id,
                reason="user_is_already_deactivated",
            )

            raise UserAlreadyInactiveError("User is already deactivated")

        target_user.is_active = False
        target_user.status = UserStatus.DEACTIVATED

        target_user.session.access_token_version += 1
        target_user.session.refresh_token_hash = None
        target_user.session.refresh_token_family = None
        target_user.session.refresh_token_expires_at = None

        await session.commit()

        asyncio.create_task(
            email_sender.send_safe(
                email_sender.send_account_deactivation_email(
                    target_user.email, target_user.role
                ),
                email_type=EmailType.ACCOUNT_DEACTIVATION,
            )
        )

        await delete_cache(
            SessionCacheKey.access_token_version_key(target_user_id),
            UserCacheKey.user_detail_key_admin(target_user_id),
            UserCacheKey.user_detail_key_staff(target_user_id),
            UserCacheKey.user_detail_key_self(target_user_id),
        )

        logger.info(
            "user_deactivated",
            target_user_id=target_user_id,
            deactivated_by=current_user_id,
        )

    @staticmethod
    async def activate_user(
        session: AsyncSession, current_user_id: int, target_user_id: int
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            session,
            target_user_id,
            excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES,
            load_login_lockout=True,
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        if target_user.is_active:
            logger.warning(
                "activate_user_failed",
                target_user_id=target_user_id,
                requested_by=current_user_id,
                reason="user_is_already_activated",
            )

            raise UserAlreadyActiveError("User is already activated")

        target_user.is_active = True
        target_user.status = UserStatus.ACTIVE

        target_user.login_lockout.failed_login_attempts = 0
        target_user.login_lockout.locked_until = None

        await session.commit()

        asyncio.create_task(
            email_sender.send_safe(
                email_sender.send_account_activation_email(target_user.email),
                email_type=EmailType.ACCOUNT_ACTIVATION,
            )
        )

        await delete_cache(UserCacheKey.user_detail_key_admin(target_user_id))

        logger.info(
            "user_activated",
            target_user_id=target_user_id,
            activated_by=current_user_id,
        )

    @staticmethod
    async def create_reset_password_request(
        session: AsyncSession,
        current_user: CurrentUser,
        target_user_id: int,
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            session,
            target_user_id,
            excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES,
            load_session=True,
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        raw_reset_token, hashed_reset_token = generate_reset_password_token()

        target_user.session.reset_password_token_hash = hashed_reset_token
        target_user.session.reset_password_token_expires_at = datetime.now(
            UTC
        ) + timedelta(minutes=settings.RESET_PASSWORD_EXPIRES_MINUTES)

        subject, html_body, text_body = email_sender.build_reset_password_email(
            raw_reset_token
        )

        PendingEmailRepository.add_pending_email(
            session,
            recipient=target_user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type=EmailType.PASSWORD_RESET_ADMIN,
            triggered_by=current_user.id,
            recipient_user_id=target_user_id,
        )

        await session.commit()

        logger.info(
            "reset_password_request_created",
            target_user_id=target_user_id,
        )

    @staticmethod
    async def resend_activation_invite(
        session: AsyncSession,
        current_user_id: int,
        target_user_id: int,
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            session,
            target_user_id,
            excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES,
            load_activation=True,
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        if target_user.status != UserStatus.PENDING_ACTIVATION:
            logger.warning(
                "activation_invite_resend_denied",
                target_user_id=target_user_id,
                actor_user_id=current_user_id,
                denial_reason="user_not_pending_activation",
            )

            raise UserAlreadyActiveError("User is already activated")

        raw_invite_token, hashed_invite_token = generate_invite_token()
        invite_token_expires_at = datetime.now(UTC) + timedelta(
            hours=settings.INVITE_TOKEN_EXPIRES_HOURS
        )

        target_user.activation.invite_token_hash = hashed_invite_token
        target_user.activation.invite_token_expires_at = invite_token_expires_at

        subject, html_body, text_body = email_sender.build_invite_email(
            raw_invite_token, target_user.username
        )

        PendingEmailRepository.add_pending_email(
            session,
            recipient=target_user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type=EmailType.INVITE,
            triggered_by=current_user_id,
            recipient_user_id=target_user.id,
        )

        await session.commit()

        logger.info(
            "activation_invite_resent",
            target_user_id=target_user_id,
            actor_user_id=current_user_id,
        )

    @staticmethod
    async def get_staff(
        session: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchUserAdmin,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:
        staff, total = await UserRepositoryAdmin.get_users_admin(
            session, skip, limit, filters, sort_by, order, allowed_roles=STAFF_ROLES
        )

        return PaginatedResponse(
            items=staff,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def get_staff_by_id(
        session: AsyncSession, target_staff_id: int
    ) -> UserResponseAdminDetailed:
        cache_key = UserCacheKey.user_detail_key_admin(target_staff_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = UserCacheSchema.model_validate(cached)

            return UserResponseAdminDetailed.model_validate(raw.model_dump())

        staff = await UserRepositoryBase.get_user_by_id(
            session, target_staff_id, allowed_roles=STAFF_ROLES
        )
        ensure_exists(staff, UserNotFoundError(HTTP404.USER))

        raw = UserCacheSchema.model_validate(staff)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return UserResponseAdminDetailed.model_validate(staff)

    @staticmethod
    async def get_students(
        db: AsyncSession,
        skip: int,
        limit: int,
        group_id: int | None,
        filters: SearchUserAdmin,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:
        students, total = await UserRepositoryAdmin.get_users_admin(
            db,
            skip,
            limit,
            filters,
            sort_by,
            order,
            allowed_roles=frozenset({UserRole.STUDENT}),
            group_id=group_id,
            load_group=True,
        )

        return PaginatedResponse(
            items=students,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def get_student_by_id(
        session: AsyncSession, target_student_id: int
    ) -> StudentResponseAdminDetailed:
        cache_key = UserCacheKey.user_detail_key_admin(target_student_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = StudentCacheSchema.model_validate(cached)

            return StudentResponseAdminDetailed.model_validate(raw.model_dump())

        student = await UserRepositoryBase.get_user_by_id(
            session,
            target_student_id,
            allowed_roles=frozenset({UserRole.STUDENT}),
            load_group=True,
        )
        ensure_exists(student, UserNotFoundError(HTTP404.USER))

        raw = StudentCacheSchema.model_validate(student)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return StudentResponseAdminDetailed.model_validate(student)
