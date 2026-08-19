from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.advisory_locks import acquire_group_capacity_lock
from src.core.caching import delete_cache, get_cache, set_cache
from src.core.logging import get_logger
from src.core.pagination import PaginatedResponse
from src.groups.exceptions.constants import HTTP404
from src.groups.exceptions.exceptions import (
    GroupAlreadyArchivedError,
    GroupArchiveBlockedError,
    GroupCapacityExceededError,
    GroupIsNotArchivedError,
    GroupNotFoundError,
    handle_group_name_year_integrity_error,
)
from src.groups.models import Group
from src.groups.repository import GroupRepository
from src.groups.schemas import (
    CreateGroupAdmin,
    GroupResponseAdmin,
    GroupResponseAdminCache,
    GroupResponseAdminDetailed,
    SearchGroupAdmin,
    UpdateGroupAdmin,
)
from src.users.repositories.user import UserRepositoryBase
from src.users.utils.exceptions import UserNotFoundError
from src.utils.base_exception import raise_unhandled_integrity_error
from src.utils.cache_keys import GroupCacheKey
from src.utils.enums import UserRole
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)


class GroupServiceAdmin:
    @staticmethod
    async def create_group(
        session: AsyncSession, current_user_id: int, create_request: CreateGroupAdmin
    ) -> Group:
        try:
            new_group = Group(**create_request.model_dump())

            session.add(new_group)
            await session.commit()
            await session.refresh(new_group)

            logger.info(
                "group_created",
                group_id=new_group.id,
                created_by=current_user_id,
            )

            return new_group

        except IntegrityError as e:
            await session.rollback()

            logger.warning(
                "group_creation_failed",
                reason="integrity_error",
                error=str(e.orig),
                requested_by=current_user_id,
            )

            handle_group_name_year_integrity_error(e)
            raise_unhandled_integrity_error(e)

    @staticmethod
    async def update_group(
        session: AsyncSession,
        current_user_id: int,
        group_id: int,
        update_request: UpdateGroupAdmin,
    ) -> None:
        target_group = await GroupRepository.get_group_by_id(session, group_id)
        ensure_exists(target_group, GroupNotFoundError(HTTP404.GROUP))

        try:
            update_object(target_group, update_request)

            await session.commit()
            await session.refresh(target_group)

            await delete_cache(
                GroupCacheKey.group_detail_key_admin(group_id),
                GroupCacheKey.group_detail_key_non_admin(group_id),
            )

            logger.info(
                "group_updated",
                group_id=group_id,
                updated_by=current_user_id,
            )

        except IntegrityError as e:
            await session.rollback()

            logger.warning(
                "group_update_failed",
                reason="integrity_error",
                error=str(e.orig),
                group_id=group_id,
                requested_by=current_user_id,
            )

            handle_group_name_year_integrity_error(e)
            raise_unhandled_integrity_error(e)

    @staticmethod
    async def archive_group(
        session: AsyncSession, current_user_id: int, group_id: int
    ) -> None:
        target_group = await GroupRepository.get_group_by_id(session, group_id)
        ensure_exists(target_group, GroupNotFoundError(HTTP404.GROUP))

        if target_group.is_archived and target_group.archived_at is not None:
            logger.warning(
                "group_archive_denied",
                group_id=group_id,
                actor_user_id=current_user_id,
                denial_reason="group_is_already_archived",
            )

            raise GroupAlreadyArchivedError("Group is already archived")

        target_group.is_archived = True
        target_group.archived_at = datetime.now(UTC)

        await session.commit()

        await delete_cache(GroupCacheKey.group_detail_key_admin(group_id))

        logger.info(
            "group_archived",
            group_id=group_id,
            archived_by=current_user_id,
        )

    @staticmethod
    async def restore_group(
        session: AsyncSession, current_user_id: int, group_id: int
    ) -> None:
        target_group = await GroupRepository.get_group_by_id(session, group_id)
        ensure_exists(target_group, GroupNotFoundError(HTTP404.GROUP))

        if not target_group.is_archived and target_group.archived_at is None:
            logger.warning(
                "group_restoration_denied",
                group_id=group_id,
                actor_user_id=current_user_id,
                denial_reason="group_is_already_restored_or_has_not_been_archived",
            )

            raise GroupIsNotArchivedError(
                "Group is already restored or has not been archived"
            )

        target_group.is_archived = False
        target_group.archived_at = None

        await session.commit()

        await delete_cache(GroupCacheKey.group_detail_key_admin(group_id))

        logger.info(
            "group_restored",
            group_id=group_id,
            restored_by=current_user_id,
        )

    @staticmethod
    async def get_groups(
        session: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchGroupAdmin,
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
    ) -> GroupResponseAdminDetailed:
        cache_key = GroupCacheKey.group_detail_key_admin(group_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = GroupResponseAdminCache.model_validate(cached)

            return GroupResponseAdminDetailed.model_validate(raw.model_dump())

        group = await GroupRepository.get_group_by_id(session, group_id)
        ensure_exists(group, GroupNotFoundError(HTTP404.GROUP))

        raw = GroupResponseAdminCache.model_validate(group)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return GroupResponseAdminDetailed.model_validate(group)
