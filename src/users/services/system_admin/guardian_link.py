from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.users.exceptions.constants import HTTP404
from src.users.exceptions.exceptions import (
    GuardianLinkAlreadyExistsError,
    GuardianLinkNotFoundError,
    GuardianSlotAlreadyFilledError,
    InvalidGuardianLinkError,
)
from src.users.models.guardian_link import StudentGuardianLink
from src.users.repositories.guardian_link import GuardianLinkRepositoryAdmin
from src.users.repositories.user import UserRepositoryBase
from src.users.schemas.guardian_link import (
    CreateGuardianLinkAdmin,
    UpdateGuardianPriorityAdmin,
)
from src.utils.enums import UserRole
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)

NON_GUARDIAN_ROLES = frozenset({UserRole.STUDENT, UserRole.SYSTEM_ADMIN})


class GuardianLinkServiceAdmin:
    @staticmethod
    async def link_guardian(
        db: AsyncSession, current_user_id: int, create_request: CreateGuardianLinkAdmin
    ) -> StudentGuardianLink:
        guardian = await UserRepositoryBase.get_user_by_id(
            db, create_request.guardian_id
        )
        student = await UserRepositoryBase.get_user_by_id(db, create_request.student_id)

        if guardian is None or guardian.role in NON_GUARDIAN_ROLES:
            logger.warning(
                "guardian_link_denied",
                actor_user_id=current_user_id,
                target_guardian_id=create_request.guardian_id,
                denial_reason="target_role_not_eligible_as_guardian",
            )

            raise InvalidGuardianLinkError(
                "This user's role is not eligible to be a guardian"
            )

        if student is None or student.role != UserRole.STUDENT:
            logger.warning(
                "guardian_link_denied",
                actor_user_id=current_user_id,
                target_student_id=create_request.student_id,
                denial_reason="target_is_not_a_student",
            )

            raise InvalidGuardianLinkError("Target student_id is not a student account")

        existing_link = await GuardianLinkRepositoryAdmin.get_guardian_link(
            db, create_request.guardian_id, create_request.student_id
        )

        if existing_link is not None:
            raise GuardianLinkAlreadyExistsError(
                "This guardian is already linked to this student"
            )

        existing_at_priority = (
            await GuardianLinkRepositoryAdmin.get_guardian_link_by_priority(
                db, create_request.student_id, create_request.priority
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

            GuardianLinkRepositoryAdmin.add_link(db, new_link)

            await db.commit()

            logger.info(
                "guardian_linked",
                actor_user_id=current_user_id,
                guardian_id=create_request.guardian_id,
                student_id=create_request.student_id,
                priority=create_request.priority.value,
            )

            return new_link
        except IntegrityError as err:
            await db.rollback()

            logger.error(
                "guardian_link_failed",
                reason="integrity_error",
                error=str(err.orig),
                actor_user_id=current_user_id,
            )

            raise GuardianSlotAlreadyFilledError(
                "This guardian link could not be created"
            ) from err

    @staticmethod
    async def unlink_guardian(
        db: AsyncSession, current_user_id: int, guardian_id: int, student_id: int
    ) -> None:
        link = await GuardianLinkRepositoryAdmin.get_guardian_link(
            db, guardian_id, student_id
        )
        ensure_exists(link, GuardianLinkNotFoundError(HTTP404.GUARDIAN_LINK))

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
        update_request: UpdateGuardianPriorityAdmin,
    ) -> StudentGuardianLink:
        link = await GuardianLinkRepositoryAdmin.get_guardian_link(
            db, guardian_id, student_id
        )
        ensure_exists(link, GuardianLinkNotFoundError(HTTP404.GUARDIAN_LINK))

        if link.priority == update_request.priority:
            return link

        existing_at_target = (
            await GuardianLinkRepositoryAdmin.get_guardian_link_by_priority(
                db, student_id, update_request.priority
            )
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
            update_object(link, update_request)

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
