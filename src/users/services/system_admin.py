from datetime import UTC, datetime, timedelta
from typing import assert_never

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.advisory_locks import acquire_student_contact_lock
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
)
from src.utils import email as email_sender
from src.utils.enums import EmailType, UserRole, UserStatus
from src.utils.exceptions import (
    CannotCreateDirectorError,
    CannotCreateSystemAdminError,
    MaxNumberOfIdenticalContactsError,
    handle_non_student_unique_contact_error,
    handle_username_integrity_error,
)

logger = get_logger(__name__)

STUDENT_MAX_SHARED_CONTACT = 3
STAFF_AND_GUARDIAN_MAX_SHARED_CONTACT = 1
BLOCKED_ROLES_VIA_API = frozenset(
    {
        UserRole.SYSTEM_ADMIN,
        UserRole.DIRECTOR,
    }
)


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
    existing_count = await UserRepositoryBase.count_users_with_contact(
        db,
        role,
        phone_number=phone_number,
        email=email,
        exclude_user_id=exclude_user_id,
    )

    if existing_count >= max_allowed:
        logger.warning(
            "user_registration_denied",
            actor_user_id=current_user_id,
            target_username=target_username,
            requested_role=resolved_role,
            denial_reason="maximum_number_of_identical_contacts_reached",
        )
        raise MaxNumberOfIdenticalContactsError(
            f"Maximum number of "
            f"{'students' if role == UserRole.STUDENT else 'staff or guardian'} "
            f"with identical contact details reached"
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
            raise
