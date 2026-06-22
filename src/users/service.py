from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging import get_logger
from src.core.security import generate_invite_token
from src.users.models import User, UserActivation, UserSession
from src.users.repositories import UserRepositoryBase
from src.users.schemas import CreateUserAdmin
from src.utils.enums import UserRole, UserStatus
from src.utils.exceptions import (
    CannotCreateDirectorError,
    CannotCreateSystemAdminError,
    MaxNumberOfIdenticalCredentialsError,
)

logger = get_logger(__name__)


class UserServiceAdmin:
    @staticmethod
    async def create_user(
        db: AsyncSession, current_user_id: int, create_request: CreateUserAdmin
    ) -> User:
        if create_request.role == UserRole.SYSTEM_ADMIN:
            logger.warning(
                "user_creation_denied",
                actor_user_id=current_user_id,
                target_email=create_request.email,
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
                requested_role=create_request.role.value,
                denial_reason="director_creation_via_api_forbidden",
            )

            raise CannotCreateDirectorError("Director creation via API is forbidden")

        students_with_identical_credentials = (
            await UserRepositoryBase.get_student_with_identical_credentials(
                db, create_request.phone_number, create_request.email
            )
        )
        if (
            students_with_identical_credentials is not None
            and students_with_identical_credentials > 3
        ):
            logger.warning(
                "user_creation_denied",
                actor_user_id=current_user_id,
                target_email=create_request.email,
                denial_reason="maximum_number_of_identical_email_and_phonenumber_reached",
            )

            raise MaxNumberOfIdenticalCredentialsError(
                "Maximum number of students with identical email and phone number reached"
            )

        parents_with_identical_credentials = (
            await UserRepositoryBase.get_parent_with_identical_credentials(
                db, create_request.phone_number, create_request.email
            )
        )
        if (
            parents_with_identical_credentials is not None
            and parents_with_identical_credentials >= 1
        ):
            logger.warning(
                "user_creation_denied",
                actor_user_id=current_user_id,
                target_email=create_request.email,
                denial_reason="maximum_number_of_identical_email_and_phonenumber_reached",
            )

            raise MaxNumberOfIdenticalCredentialsError(
                "Maximum number of parents with identical email and phone number reached"
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
                role=create_request.role,
                status=UserStatus.ACTIVE,
                is_active=False,
                created_by=current_user_id,
            )

            UserRepositoryBase.add_user(db, new_user)

            await db.flush()

            new_user_activation = UserActivation(
                user_id=new_user.id,
                invite_token_hash=hashed_invite_token,
                invite_token_expires_at=invite_token_expires_at,
            )

            new_user_session = UserSession(user_id=new_user.id)

            UserRepositoryBase.add_user(db, new_user_activation)
            UserRepositoryBase.add_user(db, new_user_session)

            await db.commit()
            await db.refresh(new_user)

            logger.info(
                "user_created",
                new_user_id=new_user.id,
                role=new_user.role,
                created_by=current_user_id,
            )

            return new_user
        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "create_user_failed",
                reason="integrity_error",
                error=str(e.orig),
                requested_by=current_user_id,
            )
            raise
