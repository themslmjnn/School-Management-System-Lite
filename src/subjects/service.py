from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from pagination import PaginatedResponse
from src.core.logging import get_logger
from src.subjects.models import Subject
from src.subjects.repository import SubjectRepository
from src.subjects.schemas import SearchSubject, SubjectCreate, SubjectUpdate
from src.utils.constants import HTTP404
from src.utils.exceptions import (
    SubjectArchiveBlockedError,
    SubjectNotFoundError,
    handle_subject_code_integrity_error,
    raise_unhandled_integrity_error,
)
from src.utils.helpers import ensure_exists, update_object

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

    @staticmethod
    async def update_subject(
        db: AsyncSession, current_user_id: int, subject_id: int, request: SubjectUpdate
    ) -> Subject:
        subject = await SubjectRepository.get_by_id(db, subject_id)
        ensure_exists(subject, SubjectNotFoundError(HTTP404.SUBJECT))

        try:
            update_object(subject, request)

            await db.commit()
            await db.refresh(subject)

            logger.info(
                "subject_updated",
                subject_id=subject_id,
                updated_by=current_user_id,
            )

            return subject

        except IntegrityError as e:
            await db.rollback()

            logger.warning(
                "subject_update_failed",
                reason="integrity_error",
                error=str(e.orig),
                subject_id=subject_id,
                requested_by=current_user_id,
            )

            handle_subject_code_integrity_error(e)
            raise_unhandled_integrity_error(e)

    @staticmethod
    async def archive_subject(
        db: AsyncSession, current_user_id: int, subject_id: int
    ) -> None:
        subject = await SubjectRepository.get_subject_by_id(db, subject_id)
        ensure_exists(subject, SubjectNotFoundError(HTTP404.SUBJECT))

        if await SubjectRepository.has_active_teaching_assignments(db, subject_id):
            logger.warning(
                "subject_archive_denied",
                subject_id=subject_id,
                actor_user_id=current_user_id,
                denial_reason="active_teaching_assignments_reference_subject",
            )

            raise SubjectArchiveBlockedError(
                "Cannot archive a subject with active teaching assignments; "
                "reassign or remove them first"
            )

        subject.is_archived = True
        subject.archived_at = datetime.now(UTC)

        await db.commit()

        logger.info(
            "subject_archived",
            subject_id=subject_id,
            archived_by=current_user_id,
        )

    @staticmethod
    async def restore_subject(
        db: AsyncSession, current_user_id: int, subject_id: int
    ) -> None:
        subject = await SubjectRepository.get_by_id(db, subject_id)
        ensure_exists(subject, SubjectNotFoundError(HTTP404.SUBJECT))

        subject.is_archived = False
        subject.archived_at = None

        await db.commit()

        logger.info(
            "subject_restored",
            subject_id=subject_id,
            restored_by=current_user_id,
        )

    @staticmethod
    async def get_subjects(
        db: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchSubject,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:
        subjects, total = await SubjectRepository.get_subjects(
            db,
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            order=order,
        )

        return PaginatedResponse(
            items=subjects, 
            total=total, 
            skip=skip, 
            limit=limit,
            has_more=skip + limit < total,
        )