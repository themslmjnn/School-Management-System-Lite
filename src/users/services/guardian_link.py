from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.users.models.guardian_link import StudentGuardianLink
from src.users.repositories.guardian_link import GuardianLinkRepository
from users.repositories.users import UserRepositoryBase
from src.users.schemas.guardian_link import (
    ChildResponse,
    CreateGuardianLink,
    UpdateGuardianPriority,
)
from src.utils.enums import UserRole
from src.utils.exceptions import (
    GuardianLinkAlreadyExistsError,
    GuardianLinkNotFoundError,
    GuardianSlotAlreadyFilledError,
    InvalidGuardianLinkError,
)

logger = get_logger(__name__)

NON_GUARDIAN_ROLES = frozenset({UserRole.STUDENT, UserRole.SYSTEM_ADMIN})


class GuardianLinkService:
    @staticmethod
    async def link(
        db: AsyncSession, current_user_id: int, link_request: CreateGuardianLink
    ) -> StudentGuardianLink:
        guardian = await UserRepositoryBase.get_user_by_id(db, link_request.guardian_id)
        student = await UserRepositoryBase.get_user_by_id(db, link_request.student_id)

        if guardian is None or guardian.role in NON_GUARDIAN_ROLES:
            logger.warning(
                "guardian_link_denied",
                actor_user_id=current_user_id,
                target_guardian_id=link_request.guardian_id,
                denial_reason="target_role_not_eligible_as_guardian",
            )
            raise InvalidGuardianLinkError(
                "This user's role is not eligible to be a guardian"
            )

        if student is None or student.role != UserRole.STUDENT:
            logger.warning(
                "guardian_link_denied",
                actor_user_id=current_user_id,
                target_student_id=link_request.student_id,
                denial_reason="target_is_not_a_student",
            )
            raise InvalidGuardianLinkError("Target student_id is not a student account")

        existing_link = await GuardianLinkRepository.get_link(
            db, link_request.guardian_id, link_request.student_id
        )
        if existing_link is not None:
            raise GuardianLinkAlreadyExistsError(
                "This guardian is already linked to this student"
            )

        existing_at_priority = await GuardianLinkRepository.get_link_by_priority(
            db, link_request.student_id, link_request.priority
        )
        if existing_at_priority is not None:
            logger.warning(
                "guardian_link_denied",
                actor_user_id=current_user_id,
                target_student_id=link_request.student_id,
                denial_reason=f"{link_request.priority.value}_guardian_slot_already_filled",
            )
            raise GuardianSlotAlreadyFilledError(
                f"Student already has a {link_request.priority.value} guardian; "
                "remove or change the existing one before adding a new one"
            )

        try:
            new_link = StudentGuardianLink(
                parent_id=link_request.guardian_id,
                student_id=link_request.student_id,
                priority=link_request.priority,
            )
            GuardianLinkRepository.add_link(db, new_link)
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            logger.error(
                "guardian_link_failed",
                reason="integrity_error",
                error=str(e.orig),
                actor_user_id=current_user_id,
            )
            raise GuardianSlotAlreadyFilledError(
                "This guardian link could not be created"
            ) from e

        logger.info(
            "guardian_linked",
            actor_user_id=current_user_id,
            guardian_id=link_request.guardian_id,
            student_id=link_request.student_id,
            priority=link_request.priority.value,
        )

        return new_link

    @staticmethod
    async def unlink(
        db: AsyncSession, current_user_id: int, guardian_id: int, student_id: int
    ) -> None:
        link = await GuardianLinkRepository.get_link(db, guardian_id, student_id)

        if link is None:
            raise GuardianLinkNotFoundError("This guardian link does not exist")

        await db.delete(link)
        await db.commit()

        logger.info(
            "guardian_unlinked",
            actor_user_id=current_user_id,
            guardian_id=guardian_id,
            student_id=student_id,
        )

    @staticmethod
    async def change_priority(
        db: AsyncSession,
        current_user_id: int,
        guardian_id: int,
        student_id: int,
        update_request: UpdateGuardianPriority,
    ) -> StudentGuardianLink:
        link = await GuardianLinkRepository.get_link(db, guardian_id, student_id)

        if link is None:
            raise GuardianLinkNotFoundError("This guardian link does not exist")

        if link.priority == update_request.priority:
            return link

        existing_at_target = await GuardianLinkRepository.get_link_by_priority(
            db, student_id, update_request.priority
        )
        if existing_at_target is not None:
            logger.warning(
                "guardian_priority_change_denied",
                actor_user_id=current_user_id,
                target_student_id=student_id,
                denial_reason=f"{update_request.priority.value}_guardian_slot_already_filled",
            )
            raise GuardianSlotAlreadyFilledError(
                f"Student already has a different {update_request.priority.value} guardian; "
                "change or remove the existing one first"
            )

        try:
            link.priority = update_request.priority
            await db.commit()
            await db.refresh(link)
        except IntegrityError as e:
            await db.rollback()
            raise GuardianSlotAlreadyFilledError(
                "Could not update priority due to a conflicting guardian slot"
            ) from e

        logger.info(
            "guardian_priority_changed",
            actor_user_id=current_user_id,
            guardian_id=guardian_id,
            student_id=student_id,
            new_priority=update_request.priority.value,
        )

        return link

    @staticmethod
    async def get_children_for_guardian(
        db: AsyncSession, guardian_id: int
    ) -> list[ChildResponse]:
        links = await GuardianLinkRepository.get_children_for_guardian(db, guardian_id)

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
