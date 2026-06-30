from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import delete_cache, get_cache, set_cache
from src.core.config import settings
from src.core.dependencies import CurrentUser
from src.core.logging import get_logger
from src.core.security import generate_invite_token, generate_reset_password_token
from src.emails.repository import PendingEmailRepository
from src.pagination import PaginatedResponse
from src.users.models.users import User, UserActivation, UserLoginLockout, UserSession
from src.users.repositories.users_admin import (
    UserRepositoryAdmin,
    UserRepositoryBase,
)
from src.users.schemas.users import (
    CreateStaffAdmin,
    CreateStudentAdmin,
    SearchUserAdmin,
    UpdateUser,
    UpdateUserEmail,
    UserResponseAdminDetailed,
)
from src.utils import email as email_sender
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.constants import HTTP404
from src.utils.enums import EmailType, UserRole, UserStatus
from src.utils.exceptions import (
    CannotCreateDirectorError,
    CannotCreateStudentError,
    CannotCreateSystemAdminError,
    MaxNumberOfIdenticalContactsError,
    UserAlreadyActiveError,
    UserAlreadyInactiveError,
    UserNotFoundError,
    handle_non_student_unique_contact_error,
    handle_username_integrity_error,
)
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)

STUDENT_MAX_SHARED_CONTACT = 3
STAFF_MAX_SHARED_CONTACT = 1
SYSTEM_ADMIN_INVISIBLE_ROLES = frozenset({UserRole.SYSTEM_ADMIN})
DIRECTOR_INVISIBLE_ROLES = frozenset({UserRole.SYSTEM_ADMIN, UserRole.PARENT})
VICE_DIRECTOR_INVISIBLE_ROLES = frozenset(
    {UserRole.SYSTEM_ADMIN, UserRole.DIRECTOR, UserRole.VICE_DIRECTOR, UserRole.PARENT}
)


async def _check_contact_limit(
    db: AsyncSession,
    current_user_id: int,
    create_request: CreateStaffAdmin | CreateStudentAdmin,
    *,
    role: UserRole | None,
    max_allowed: int,
) -> None:
    existing_count = await UserRepositoryBase.count_users_with_contact(
        db,
        role,
        phone_number=create_request.phone_number,
        email=create_request.email,
    )

    if existing_count >= max_allowed:
        logger.warning(
            "user_registration_denied",
            actor_user_id=current_user_id,
            target_username=create_request.username,
            requested_role=UserRole.STUDENT
            if role == UserRole.STUDENT
            else create_request.role,
            denial_reason="maximum_number_of_identical_contacts_reached",
        )

        raise MaxNumberOfIdenticalContactsError(
            f"Maximum number of {'students' if role == UserRole.STUDENT else 'staff'} with identical contact details reached"
        )


class UserServiceAdmin:
    @staticmethod
    async def register_staff(
        db: AsyncSession, current_user_id: int, create_request: CreateStaffAdmin
    ) -> User:
        if create_request.role == UserRole.SYSTEM_ADMIN:
            logger.warning(
                "user_registration_denied",
                actor_user_id=current_user_id,
                target_username=create_request.username,
                requested_role=create_request.role.value,
                denial_reason="system_admin_creation_via_api_is_forbidden",
            )

            raise CannotCreateSystemAdminError(
                "System admin creation via API is forbidden"
            )

        if create_request.role == UserRole.DIRECTOR:
            logger.warning(
                "user_creation_denied",
                actor_user_id=current_user_id,
                target_username=create_request.username,
                requested_role=create_request.role.value,
                denial_reason="director_creation_via_api_is_forbidden",
            )

            raise CannotCreateDirectorError("Director creation via API is forbidden")

        if create_request.role == UserRole.STUDENT:
            logger.warning(
                "user_creation_denied",
                actor_user_id=current_user_id,
                target_username=create_request.username,
                requested_role=UserRole.STUDENT,
                denial_reason="student_creation_via_staff_service_is_forbidden",
            )

            raise CannotCreateStudentError(
                "Student creation via staff service is forbidden"
            )

        await _check_contact_limit(
            db,
            current_user_id,
            create_request,
            role=None,
            max_allowed=STAFF_MAX_SHARED_CONTACT,
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
                role=create_request.role,
                status=UserStatus.PENDING_ACTIVATION,
                is_active=False,
                created_by=current_user_id,
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
                raw_invite_token, new_user.email
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

            print(f"Invite token: {raw_invite_token}")

            await db.commit()
            await db.refresh(new_user)

            logger.info(
                "user_registered",
                new_user_id=new_user.id,
                target_username=create_request.username,
                role=new_user.role,
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
            handle_non_student_unique_contact_error(e)
            raise

    @staticmethod
    async def register_student(
        db: AsyncSession, current_user_id: int, create_request: CreateStudentAdmin
    ) -> User:

        await _check_contact_limit(
            db,
            current_user_id,
            create_request,
            role=UserRole.STUDENT,
            max_allowed=STUDENT_MAX_SHARED_CONTACT,
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
                date_of_birth=create_request.date_of_birth,
                phone_number=create_request.phone_number,
                email=create_request.email,
                address=create_request.address,
                role=UserRole.STUDENT,
                status=UserStatus.PENDING_ACTIVATION,
                is_active=False,
                created_by=current_user_id,
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
                raw_invite_token, new_user.email
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

            print(f"Invite token: {raw_invite_token}")

            await db.commit()
            await db.refresh(new_user)

            logger.info(
                "user_registered",
                new_user_id=new_user.id,
                target_username=create_request.username,
                role=UserRole.STUDENT,
                created_by=current_user_id,
            )

            return new_user
        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "user_registration_failed",
                reason="integrity_error",
                error=str(e.orig),
                requested_by=current_user_id,
            )

            handle_username_integrity_error(e)
            raise

    @staticmethod
    async def delete_parent(
        db: AsyncSession, current_user_id: int, parent_id: int
    ) -> None:
        user_to_be_deleted = await UserRepositoryBase.get_parent(db, parent_id)
        ensure_exists(user_to_be_deleted, UserNotFoundError(HTTP404.USER))

        UserRepositoryBase.delete_user(db, user_to_be_deleted)

        deleted_user_id, deleted_user_username = (
            user_to_be_deleted.id,
            user_to_be_deleted.username,
        )

        await db.commit()

        logger.info(
            "user_successfully_deleted",
            deleted_user_id=deleted_user_id,
            deleted_user_username=deleted_user_username,
            deleted_user_role=UserRole.PARENT,
            deleted_by=current_user_id,
        )

    @staticmethod
    async def deactivate_user(
        db: AsyncSession, current_user_id: int, user_id: int
    ) -> None:
        user = await UserRepositoryBase.get_user_by_id(
            db, user_id, load_session=True, excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES
        )
        ensure_exists(user, UserNotFoundError(HTTP404.USER))

        if not user.is_active:
            logger.error(
                "deactivate_user_failed",
                target_user_id=user_id,
                requested_by=current_user_id,
                reason="user_is_already_deactivated",
            )

            raise UserAlreadyInactiveError("User is already deactivated")

        user.is_active = False
        user.session.access_token_version += 1
        user.session.refresh_token_hash = None
        user.session.refresh_token_family = None
        user.session.refresh_token_expires_at = None

        await db.commit()

        await delete_cache(
            UserCacheKey.user_detail_key_admin(user_id),
            SessionCacheKey.access_token_version_key(user_id),
        )

        logger.info(
            "user_deactivated",
            target_user_id=user_id,
            deactivated_by=current_user_id,
        )

    @staticmethod
    async def activate_user(
        db: AsyncSession, current_user_id: int, user_id: int
    ) -> None:
        user = await UserRepositoryBase.get_user_by_id(
            db, user_id, excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES
        )
        ensure_exists(user, UserNotFoundError(HTTP404.USER))

        if user.is_active:
            logger.error(
                "activate_user_failed",
                target_user_id=user_id,
                requested_by=current_user_id,
                reason="user_is_already_activated",
            )

            raise UserAlreadyActiveError("User is already activated")

        user.is_active = True

        await db.commit()

        await delete_cache(UserCacheKey.user_detail_key_admin(user_id))

        logger.info(
            "user_activated",
            target_user_id=user_id,
            activated_by=current_user_id,
        )

    @staticmethod
    async def update_user(
        db: AsyncSession,
        current_user_id: int,
        user_id: int,
        update_request: UpdateUser,
    ) -> User:
        user = await UserRepositoryBase.get_user_by_id(
            db, user_id, excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES
        )
        ensure_exists(user, UserNotFoundError(HTTP404.USER))

        try:
            update_object(user, update_request)

            await db.commit()
            await db.refresh(user)

            await delete_cache(
                UserCacheKey.user_detail_key_admin(user_id),
                UserCacheKey.user_detail_key_staff(user_id),
                UserCacheKey.user_detail_key_self(user_id),
            )

            logger.info(
                "user_updated",
                target_user_id=user_id,
                updated_by=current_user_id,
                method="admin_update",
            )

            return user
        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "update_user_denied",
                target_user_id=user_id,
                requested_by=current_user_id,
                reason=str(e.orig),
            )

            handle_username_integrity_error(e)
            handle_non_student_unique_contact_error(e)
            raise

    @staticmethod
    async def update_user_email(
        db: AsyncSession,
        current_user_id: int,
        user_id: int,
        update_request: UpdateUserEmail,
    ) -> None:
        user = await UserRepositoryBase.get_user_by_id(
            db, user_id, excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES, load_session=True
        )
        ensure_exists(user, UserNotFoundError(HTTP404.USER))

        try:
            # old_email = user.email
            user.email = update_request.new_email

            user.session.access_token_version += 1
            user.session.refresh_token_hash = None
            user.session.refresh_token_family = None
            user.session.refresh_token_expires_at = None

            user.session.pending_new_email = None
            user.session.email_change_code_hash = None
            user.session.email_change_code_expires_at = None

            await db.commit()

            await delete_cache(
                UserCacheKey.user_detail_key_admin(user_id),
                UserCacheKey.user_detail_key_staff(user_id),
                UserCacheKey.user_detail_key_self(user_id),
                SessionCacheKey.access_token_version_key(user_id),
            )

            logger.info(
                "admin_email_override",
                target_user_id=user_id,
                updated_by=current_user_id,
            )

        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "admin_email_override_failed",
                target_user_id=user_id,
                requested_by=current_user_id,
                reason=str(e.orig),
            )

            handle_non_student_unique_contact_error(e)
            raise

    @staticmethod
    async def create_reset_password_request(
        db: AsyncSession,
        current_user: CurrentUser,
        user_id: int,
    ) -> None:

        user = await UserRepositoryBase.get_user_by_id(
            db,
            user_id,
            excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES,
            load_session=True,
        )

        ensure_exists(user, UserNotFoundError(HTTP404.USER))

        raw_reset_token, hashed_reset_token = generate_reset_password_token()

        user.session.reset_password_token_hash = hashed_reset_token
        user.session.reset_password_token_expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.RESET_PASSWORD_EXPIRES_MINUTES
        )

        subject, html_body, text_body = email_sender.build_reset_password_email(
            raw_reset_token
        )

        PendingEmailRepository.create(
            db,
            recipient=user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type=EmailType.password_reset_admin,
            triggered_by=current_user.id,
            recipient_user_id=user.id,
        )

        await db.commit()

        logger.info(
            "reset_password_request_created",
            user_id=user.id,
        )

    @staticmethod
    async def get_users(
        db: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchUserAdmin,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:

        users, total = await UserRepositoryAdmin.get_users_admin(
            db, skip, limit, filters, sort_by, order
        )

        return PaginatedResponse(
            items=users,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession, user_id: int
    ) -> UserResponseAdminDetailed | dict:
        cache_key = UserCacheKey.user_detail_key_admin(user_id)
        cached = await get_cache(cache_key)
        if cached is not None:
            return cached

        user = await UserRepositoryBase.get_user_by_id(
            db, user_id, excluded_roles=SYSTEM_ADMIN_INVISIBLE_ROLES
        )
        ensure_exists(user, UserNotFoundError(HTTP404.USER))

        result = UserResponseAdminDetailed.model_validate(user)
        await set_cache(
            cache_key,
            result.model_dump(mode="json"),
            900,
        )

        return result


class UserServiceStaff:
    @staticmethod
    async def get_users(
        db: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchUserAdmin,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:

        users, total = await UserRepositoryAdmin.get_users(
            db,
            excluded_roles=DIRECTOR_INVISIBLE_ROLES,
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            order=order,
        )

        return PaginatedResponse(
            items=users,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )
