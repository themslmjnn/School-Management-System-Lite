from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import get_cache, set_cache
from src.core.pagination import PaginatedResponse
from src.emails.repository import PendingEmailRepository
from src.emails.schemas import (
    PendingEmailResponseCache,
    PendingEmailResponseDetailed,
    SearchEmailAdmin,
)
from src.utils.cache_keys import EmailCacheKey
from src.utils.constants import HTTP404
from src.utils.enums import EmailSortField, OrderBy
from src.utils.exceptions import PendingEmailNotFoundError
from src.utils.helpers import ensure_exists


class PendingEmailService:
    @staticmethod
    async def get_emails(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        filters: SearchEmailAdmin | None = None,
        sort_by: str = EmailSortField.CREATED_AT,
        order: str = OrderBy.DESC,
    ) -> PaginatedResponse:
        emails, total = await PendingEmailRepository.get_emails(
            session,
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            order=order,
        )

        return PaginatedResponse(
            items=emails,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def get_email_by_id(
        session: AsyncSession,
        email_id: int,
    ) -> PendingEmailResponseDetailed:
        cache_key = EmailCacheKey.email_detail_key(email_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = PendingEmailResponseCache.model_validate(cached)
            return PendingEmailResponseDetailed.model_validate(raw.model_dump())

        email = await PendingEmailRepository.get_email_by_id(session, email_id)
        ensure_exists(email, PendingEmailNotFoundError(HTTP404.PENDING_EMAIL))

        raw = PendingEmailResponseCache.model_validate(email)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return PendingEmailResponseDetailed.model_validate(email)

    @staticmethod
    async def retry_failed_email(
        session: AsyncSession,
        email_id: int,
    ) -> None:
        failed_email = await PendingEmailRepository.get_email_by_id(session, email_id)
        ensure_exists(failed_email, PendingEmailNotFoundError(HTTP404.PENDING_EMAIL))

        await PendingEmailRepository.reset_for_retry(session, failed_email)

        await session.commit()
