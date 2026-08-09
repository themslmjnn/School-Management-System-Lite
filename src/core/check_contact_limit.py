from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.users.exceptions.exceptions import (
    MaxStaffOrGuardianPerEmailError,
    MaxStaffOrGuardianPerPhoneNumberError,
    MaxStudentsPerEmailError,
    MaxStudentsPerPhoneNumberError,
)
from src.users.repositories.user import UserRepositoryBase
from src.utils.enums import UserRole

logger = get_logger(__name__)


async def check_contact_limit(
    session: AsyncSession,
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
            session,
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
            session,
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
