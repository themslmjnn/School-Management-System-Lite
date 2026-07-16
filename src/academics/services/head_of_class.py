from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.academics.models.head_of_class_assignment import HeadOfClassAssignment
from src.academics.repositories.head_of_class import HeadOfClassRepository
from src.academics.schemas.head_of_class import HeadOfClassCreate
from src.core.logging import get_logger
from utils.base_exception import (
    HeadOfClassSlotAlreadyFilledError,
    TeacherAlreadyHeadOfClassForGroupError,
)

logger = get_logger(__name__)


class HeadOfClassService:
    @staticmethod
    async def assign(
        db: AsyncSession,
        current_user_id: int,
        group_id: int,
        request: HeadOfClassCreate,
    ) -> HeadOfClassAssignment:
        existing_assignments = await HeadOfClassRepository.get_by_group(db, group_id)

        role_holder = next(
            (a for a in existing_assignments if a.role == request.role), None
        )

        if role_holder is not None:
            logger.warning(
                "head_of_class_assignment_denied",
                group_id=group_id,
                actor_user_id=current_user_id,
                denial_reason=f"{request.role.value.lower()}_slot_already_filled",
            )

            raise HeadOfClassSlotAlreadyFilledError(
                f"Group already has a {request.role.value.lower()} "
                "head-of-class teacher; remove or change the existing one first"
            )

        teacher_already_assigned = any(
            a.teacher_id == request.teacher_id for a in existing_assignments
        )
        if teacher_already_assigned:
            logger.warning(
                "head_of_class_assignment_denied",
                group_id=group_id,
                actor_user_id=current_user_id,
                denial_reason="teacher_already_head_of_class_for_group",
            )
            raise TeacherAlreadyHeadOfClassForGroupError(
                "This teacher already holds a head-of-class role for this group"
            )

        assignment = HeadOfClassAssignment(
            group_id=group_id,
            teacher_id=request.teacher_id,
            role=request.role,
        )

        try:
            HeadOfClassRepository.add_head_of_class(db, assignment)
            await db.commit()
            await db.refresh(assignment)

        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "head_of_class_assignment_race_lost",
                group_id=group_id,
                teacher_id=request.teacher_id,
                role=request.role.value,
                actor_user_id=current_user_id,
            )

            raise HeadOfClassSlotAlreadyFilledError(
                "This head-of-class assignment could not be created"
            ) from e

        logger.info(
            "head_of_class_assigned",
            group_id=group_id,
            teacher_id=request.teacher_id,
            role=request.role.value,
            assigned_by=current_user_id,
        )

        return assignment
