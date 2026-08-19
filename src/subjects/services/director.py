from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import get_cache, set_cache
from src.core.pagination import PaginatedResponse
from src.subjects.exceptions.constants import HTTP404
from src.subjects.exceptions.exceptions import SubjectNotFoundError
from src.subjects.repository import SubjectRepository
from src.subjects.schemas import (
    SearchSubjectBase,
    SubjectResponseBase,
    SubjectResponseDirectorCache,
)
from src.utils.cache_keys import SubjectCacheKey
from src.utils.helpers import ensure_exists


class SubjectServiceDirector:
    @staticmethod
    async def get_subjects(
        session: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchSubjectBase,
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
    ) -> SubjectResponseBase:
        cache_key = SubjectCacheKey.subject_detail_key_staff(subject_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = SubjectResponseDirectorCache.model_validate(cached)
            return SubjectResponseBase.model_validate(raw.model_dump())

        subject = await SubjectRepository.get_subject_by_id(session, subject_id)
        ensure_exists(subject, SubjectNotFoundError(HTTP404.SUBJECT))

        raw = SubjectResponseDirectorCache.model_validate(subject)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return SubjectResponseBase.model_validate(subject)
