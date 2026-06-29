import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging import get_logger
from src.core.security import generate_invite_token
from src.emails.repository import PendingEmailRepository
from src.users.models.users import User, UserActivation, UserLoginLockout, UserSession
from src.users.repositories.users import UserRepositoryBase
from src.users.schemas.users import CreateStaffAdmin, CreateStudentAdmin
from src.utils import email as email_sender
from src.utils.constants import HTTP400, HTTP404
from src.utils.enums import EmailType, UserRole, UserStatus
from src.utils.exceptions import (
    CannotCreateDirectorError,
    CannotCreateSystemAdminError,
    DateOfBirthNullError,
    MaxNumberOfIdenticalContactError,
    UserNotFoundError,
    handle_non_student_unique_contact_error,
    handle_username_integrity_error,
)
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)

STUDENT_MAX_SHARED_CONTACT = 3
STAFF_MAX_SHARED_CONTACT = 1


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
            "user_creation_denied",
            actor_user_id=current_user_id,
            target_email=create_request.email,
            target_username=create_request.username,
            requested_role=create_request.role,
            denial_reason="maximum_number_of_identical_contact_reached",
        )
        raise MaxNumberOfIdenticalContactError(
            f"Maximum number of {role.value}s with identical contact details reached"
        )


class UserServiceAdmin:
    @staticmethod
    async def create_staff(
        db: AsyncSession, current_user_id: int, create_request: CreateStaffAdmin
    ) -> User:
        if create_request.role == UserRole.SYSTEM_ADMIN:
            logger.warning(
                "user_creation_denied",
                actor_user_id=current_user_id,
                target_email=create_request.email,
                target_username=create_request.username,
                requested_role=create_request.role.value,
                denial_reason="system_admin_creation_via_api_forbidden",
            )

            raise CannotCreateSystemAdminError(
                "System admin creation via API is forbidden"
            )

        if create_request.role == UserRole.DIRECTOR:
            logger.warning(
                "user_creation_denied",
                actor_user_id=current_user_id,
                target_email=create_request.email,
                target_username=create_request.username,
                requested_role=create_request.role.value,
                denial_reason="director_creation_via_api_forbidden",
            )

            raise CannotCreateDirectorError("Director creation via API is forbidden")

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

            await db.commit()
            await db.refresh(new_user)

            logger.info(
                "user_created",
                new_user_id=new_user.id,
                target_username=create_request.username,
                role=new_user.role,
                created_by=current_user_id,
            )

            return new_user
        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "user_creation_failed",
                reason="integrity_error",
                error=str(e.orig),
                requested_by=current_user_id,
            )

            handle_username_integrity_error(e)
            handle_non_student_unique_contact_error(e)
            raise

    @staticmethod
    async def create_student(
        db: AsyncSession, current_user_id: int, create_request: CreateStudentAdmin
    ) -> User:
        if create_request.role == UserRole.STUDENT:
            await _check_contact_limit(
                db,
                current_user_id,
                create_request,
                role=UserRole.STUDENT,
                max_allowed=STUDENT_MAX_SHARED_CONTACT,
            )

        if create_request.date_of_birth is None:
            logger.warning(
                "date_of_birth_is_none",
                actor_user_id=current_user_id,
                target_email=create_request.email,
                target_username=create_request.username,
                requested_role=create_request.role.value,
                denial_reason="students_date_of_birth_field_must_not_be_none",
            )

            raise DateOfBirthNullError(HTTP400.DATE_OF_BIRTH)

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

            await db.commit()
            await db.refresh(new_user)

            logger.info(
                "user_created",
                new_user_id=new_user.id,
                target_username=create_request.username,
                role=new_user.role,
                created_by=current_user_id,
            )

            return new_user
        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "user_creation_failed",
                reason="integrity_error",
                error=str(e.orig),
                requested_by=current_user_id,
            )

            handle_username_integrity_error(e)
            raise

    @staticmethod
    async def delete_parent(db: AsyncSession, current_user_id: int, target_user_id: int) -> None:
        user_to_be_deleted = await UserRepositoryBase.get_parent(db, target_user_id)
        ensure_exists(user_to_be_deleted, UserNotFoundError(HTTP404.USER))

        UserRepositoryBase.delete_user(db, user_to_be_deleted)
        
        asyncio.create_task(
            email_sender.send_safe(
                email_sender.send_user_deletion_email(),
                email_type="account_deletion",
            )
        )
        
        deleted_user_id, deleted_user_username = user_to_be_deleted.id, user_to_be_deleted.username

        await db.commit()

        logger.info(
            "user_successfully_delete",
            deleted_user_id=deleted_user_id,
            deleted_user_username=deleted_user_username,
            deleted_user_role=UserRole.PARENT,
            delete_by=current_user_id,
        )

