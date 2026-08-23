from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import get_cache, set_cache
from src.core.logging import get_logger
from src.core.pagination import PaginatedResponse
from src.groups.repository import GroupRepository
from src.groups.schemas import (
    GroupResponseDirectorCache,
    GroupResponseDirectorDetailed,
    SearchGroupBase,
)
from src.utils.cache_keys import GroupCacheKey
from src.utils.constants import HTTP404
from src.utils.exceptions import GroupNotFoundError
from src.utils.helpers import ensure_exists

logger = get_logger(__name__)


class GroupServiceDirector:
    @staticmethod
    async def get_groups(
        session: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchGroupBase,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:
        groups, total = await GroupRepository.get_groups(
            session,
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            order=order,
        )

        return PaginatedResponse(
            items=groups,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def get_group_by_id(
        session: AsyncSession, group_id: int
    ) -> GroupResponseDirectorDetailed:
        cache_key = GroupCacheKey.group_detail_key_non_admin(group_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = GroupResponseDirectorCache.model_validate(cached)
            return GroupResponseDirectorDetailed.model_validate(raw.model_dump())

        group = await GroupRepository.get_group_by_id(session, group_id)
        ensure_exists(group, GroupNotFoundError(HTTP404.GROUP))

        raw = GroupResponseDirectorCache.model_validate(group)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return GroupResponseDirectorDetailed.model_validate(group)
