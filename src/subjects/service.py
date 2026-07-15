from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from subjects.models import Subject
from subjects.repository import SubjectRepository
from subjects.schemas import SubjectCreate
from utils.exceptions import (
    handle_subject_code_integrity_error,
    raise_unhandled_integrity_error,
)

logger = get_logger(__name__)


class SubjectService:
    @staticmethod
    async def create_subject(
        db: AsyncSession, current_user_id: int, request: SubjectCreate
    ) -> Subject:
        try:
            new_subject = Subject(**request.model_dump())
            SubjectRepository.add_subject(db, new_subject)

            await db.commit()
            await db.refresh(new_subject)

            logger.info(
                "subject_created",
                subject_id=new_subject.id,
                created_by=current_user_id,
            )

            return new_subject

        except IntegrityError as e:
            await db.rollback()

            logger.warning(
                "subject_creation_failed",
                reason="integrity_error",
                error=str(e.orig),
                requested_by=current_user_id,
            )

            handle_subject_code_integrity_error(e)
            raise_unhandled_integrity_error(e)
