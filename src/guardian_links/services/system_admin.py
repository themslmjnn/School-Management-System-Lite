from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.guardian_links.models import StudentGuardianLink
from src.guardian_links.repository import GuardianLinkRepository
from src.guardian_links.schemas import (
    CreateGuardianLinkAdmin,
    GuardianLinkResponseAdmin,
)
from src.guardian_links.utils.exceptions import (
    GuardianLinkAlreadyExistsError,
    GuardianSlotAlreadyFilledError,
    InvalidGuardianLinkError,
    handle_guardian_student_pair_error,
    handle_one_primary_guardian_per_student_error,
    handle_one_secondary_guardian_per_student_error,
)
from src.guardian_links.utils.helpers import build_guardian_link_response_admin
from src.users.repositories.user import UserRepositoryBase
from src.utils.base_exception import raise_unhandled_integrity_error
from src.utils.enums import UserRole

logger = get_logger(__name__)

NON_GUARDIAN_ROLES = frozenset({UserRole.STUDENT, UserRole.SYSTEM_ADMIN})


class GuardianLinkServiceAdmin:
    @staticmethod
    async def link_guardian(
        session: AsyncSession,
        current_user_id: int,
        create_request: CreateGuardianLinkAdmin,
    ) -> GuardianLinkResponseAdmin:
        guardian = await UserRepositoryBase.get_user_by_id(
            session, create_request.guardian_id
        )
        student = await UserRepositoryBase.get_user_by_id(
            session, create_request.student_id
        )

        if guardian is None or guardian.role in NON_GUARDIAN_ROLES:
            logger.warning(
                "guardian_link_creation_denied",
                actor_user_id=current_user_id,
                target_guardian_id=create_request.guardian_id,
                denial_reason="target_role_not_eligible_as_guardian",
            )

            raise InvalidGuardianLinkError(
                "This user's role is not eligible to be a guardian"
            )

        if student is None or student.role != UserRole.STUDENT:
            logger.warning(
                "guardian_link_creation_denied",
                actor_user_id=current_user_id,
                target_student_id=create_request.student_id,
                denial_reason="target_is_not_a_student",
            )

            raise InvalidGuardianLinkError("Target student_id is not a student account")

        existing_link = await GuardianLinkRepository.get_guardian_link(
            session, create_request.guardian_id, create_request.student_id
        )
        if existing_link is not None:
            logger.warning(
                "guardian_link_creation_denied",
                target_guardian_id=create_request.guardian_id,
                target_student_id=create_request.student_id,
                actor_user_id=current_user_id,
                denial_reason="guardian_already_linked_to_student",
            )

            raise GuardianLinkAlreadyExistsError(
                "This guardian is already linked to this student"
            )

        existing_at_priority = (
            await GuardianLinkRepository.get_guardian_link_by_priority(
                session, create_request.student_id, create_request.priority
            )
        )
        if existing_at_priority is not None:
            logger.warning(
                "guardian_link_denied",
                actor_user_id=current_user_id,
                target_student_id=create_request.student_id,
                denial_reason=f"{create_request.priority.value}_guardian_slot_already_filled",
            )

            raise GuardianSlotAlreadyFilledError(
                f"Student already has a {create_request.priority.value} guardian; "
                "remove or change the existing one before adding a new one"
            )

        try:
            new_link = StudentGuardianLink(
                guardian_id=create_request.guardian_id,
                student_id=create_request.student_id,
                priority=create_request.priority,
            )

            session.add(new_link)
            await session.flush()

            loaded_link = await GuardianLinkRepository.get_link_by_id(
                session, new_link.id
            )

            await session.commit()

            logger.info(
                "guardian_linked",
                actor_user_id=current_user_id,
                guardian_id=create_request.guardian_id,
                student_id=create_request.student_id,
                priority=create_request.priority.value,
            )

            return build_guardian_link_response_admin(loaded_link)

        except IntegrityError as err:
            await session.rollback()

            logger.error(
                "guardian_link_creation_failed",
                reason="integrity_error",
                error=str(err.orig),
                actor_user_id=current_user_id,
            )

            handle_guardian_student_pair_error(err)
            handle_one_primary_guardian_per_student_error(err)
            handle_one_secondary_guardian_per_student_error(err)
            raise_unhandled_integrity_error(err)
