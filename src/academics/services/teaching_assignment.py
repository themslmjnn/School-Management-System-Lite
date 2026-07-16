from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.academics.models.teaching_assignment import TeachingAssignment
from src.academics.repositories.teaching_assignment import TeachingAssignmentRepository
from src.academics.schemas.teaching_assingment import TeachingAssignmentCreate
from src.core.logging import get_logger
from utils.base_exception import TeachingAssignmentAlreadyExistsError

logger = get_logger(__name__)


class TeachingAssignmentService:
    @staticmethod
    async def create_assignment(
        db: AsyncSession, current_user_id: int, request: TeachingAssignmentCreate
    ) -> TeachingAssignment:
        assignment = TeachingAssignment(**request.model_dump())
        try:
            TeachingAssignmentRepository.add_assignment(db, assignment)
            await db.commit()
            await db.refresh(assignment)

        except IntegrityError as e:
            await db.rollback()
            raise TeachingAssignmentAlreadyExistsError(
                "This teacher-subject-group assignment already exists"
            ) from e

        logger.info(
            "teaching_assignment_created",
            assignment_id=assignment.id,
            created_by=current_user_id,
        )

        return assignment

    @staticmethod
    async def delete_assignment(
        db: AsyncSession, current_user_id: int, assignment_id: int
    ) -> None:
        assignment = await TeachingAssignmentRepository.get_by_id(db, assignment_id)
        # ensure_exists(assignment, SubjectNotFoundError(HTTP404.USER))  # placeholder

        await db.delete(assignment)
        await db.commit()

        logger.info(
            "teaching_assignment_deleted",
            assignment_id=assignment_id,
            deleted_by=current_user_id,
        )
