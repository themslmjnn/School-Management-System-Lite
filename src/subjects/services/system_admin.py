from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import delete_cache, get_cache, set_cache
from src.core.logging import get_logger
from src.core.pagination import PaginatedResponse
from src.subjects.exceptions.constants import HTTP404
from src.subjects.exceptions.exceptions import (
    SubjectAlreadyArchivedError,
    SubjectNotArchivedError,
    SubjectNotFoundError,
    handle_subject_code_integrity_error,
)
from src.subjects.models import Subject
from src.subjects.repository import SubjectRepository
from src.subjects.schemas import (
    CreateSubjectAdmin,
    SearchSubjectAdmin,
    SubjectResponseAdminCache,
    SubjectResponseAdminDetailed,
    UpdateSubjectAdmin,
)
from src.utils.base_exception import raise_unhandled_integrity_error
from src.utils.cache_keys import SubjectCacheKey
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)


class SubjectServiceAdmin:
    @staticmethod
    async def create_subject(
        session: AsyncSession, current_user_id: int, create_request: CreateSubjectAdmin
    ) -> Subject:
        try:
            new_subject = Subject(**create_request.model_dump())

            session.add(new_subject)
            await session.commit()
            await session.refresh(new_subject)

            logger.info(
                "subject_created",
                subject_id=new_subject.id,
                created_by=current_user_id,
            )

            return new_subject

        except IntegrityError as e:
            await session.rollback()

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
        session: AsyncSession,
        current_user_id: int,
        subject_id: int,
        request: UpdateSubjectAdmin,
    ) -> Subject:
        target_subject = await SubjectRepository.get_subject_by_id(session, subject_id)
        ensure_exists(target_subject, SubjectNotFoundError(HTTP404.SUBJECT))

        try:
            update_object(target_subject, request)

            await session.commit()
            await session.refresh(target_subject)

            await delete_cache(
                SubjectCacheKey.subject_detail_key_admin(subject_id),
                SubjectCacheKey.subject_detail_key_non_admin(subject_id),
            )

            logger.info(
                "subject_updated",
                subject_id=subject_id,
                updated_by=current_user_id,
            )

        except IntegrityError as e:
            await session.rollback()

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
        session: AsyncSession, current_user_id: int, subject_id: int
    ) -> None:
        target_subject = await SubjectRepository.get_subject_by_id(session, subject_id)
        ensure_exists(target_subject, SubjectNotFoundError(HTTP404.SUBJECT))

        if target_subject.is_archived or target_subject.archived_at is not None:
            logger.warning(
                "subject_archive_denied",
                subject_id=subject_id,
                actor_user_id=current_user_id,
                denial_reason="subject_is_already_archived",
            )

            raise SubjectAlreadyArchivedError("Subject is already archived")

        target_subject.is_archived = True
        target_subject.archived_at = datetime.now(UTC)

        await session.commit()

        await delete_cache(SubjectCacheKey.subject_detail_key_admin(subject_id))

        logger.info(
            "subject_archived",
            subject_id=subject_id,
            archived_by=current_user_id,
        )

    @staticmethod
    async def restore_subject(
        session: AsyncSession, current_user_id: int, subject_id: int
    ) -> None:
        target_subject = await SubjectRepository.get_subject_by_id(session, subject_id)
        ensure_exists(target_subject, SubjectNotFoundError(HTTP404.SUBJECT))

        if not target_subject.is_archived or target_subject.archived_at is None:
            logger.warning(
                "subject_restoration_denied",
                subject_id=subject_id,
                actor_user_id=current_user_id,
                denial_reason="subject_is_already_restored_or_has_not_been_archived",
            )

            raise SubjectNotArchivedError(
                "Subject is already restored or has not been archived"
            )

        target_subject.is_archived = False
        target_subject.archived_at = None

        await session.commit()

        await delete_cache(SubjectCacheKey.subject_detail_key_admin(subject_id))

        logger.info(
            "subject_restored",
            subject_id=subject_id,
            restored_by=current_user_id,
        )

    @staticmethod
    async def get_subjects(
        session: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchSubjectAdmin,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:
        subjects, total = await SubjectRepository.get_subjects(
            session,
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

    @staticmethod
    async def get_subject_by_id(
        session: AsyncSession, subject_id: int
    ) -> SubjectResponseAdminDetailed:
        cache_key = SubjectCacheKey.subject_detail_key_admin(subject_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = SubjectResponseAdminCache.model_validate(cached)

            return SubjectResponseAdminDetailed.model_validate(raw.model_dump())

        subject = await SubjectRepository.get_subject_by_id(session, subject_id)
        ensure_exists(subject, SubjectNotFoundError(HTTP404.SUBJECT))

        raw = SubjectResponseAdminCache.model_validate(subject)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return SubjectResponseAdminDetailed.model_validate(subject)
