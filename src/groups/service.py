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
    GroupCacheSchema,
    GroupCreate,
    GroupResponse,
    GroupUpdate,
    SearchGroup,
)
from src.users.exceptions.exceptions import UserNotFoundError
from src.users.repositories.user import UserRepositoryBase
from src.utils.base_exception import raise_unhandled_integrity_error
from src.utils.cache_keys import GroupCacheKey
from src.utils.enums import UserRole
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)


class GroupService:
    @staticmethod
    async def create_group(
        db: AsyncSession, current_user_id: int, create_request: GroupCreate
    ) -> Group:
        try:
            new_group = Group(**create_request.model_dump())

            GroupRepository.add_group(db, new_group)

            await db.commit()
            await db.refresh(new_group)

            logger.info(
                "group_created",
                group_id=new_group.id,
                created_by=current_user_id,
            )

            return new_group

        except IntegrityError as e:
            await db.rollback()

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
        db: AsyncSession,
        current_user_id: int,
        group_id: int,
        update_request: GroupUpdate,
    ) -> Group:
        target_group = await GroupRepository.get_group_by_id(db, group_id)
        ensure_exists(target_group, GroupNotFoundError(HTTP404.GROUP))

        try:
            update_object(target_group, update_request)

            await db.commit()
            await db.refresh(target_group)

            logger.info(
                "group_updated",
                group_id=group_id,
                updated_by=current_user_id,
            )

            await delete_cache(
                GroupCacheKey.group_detail_key_admin(group_id),
                GroupCacheKey.group_detail_key_non_admin(group_id),
            )

            return target_group

        except IntegrityError as e:
            await db.rollback()

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
        db: AsyncSession, current_user_id: int, group_id: int
    ) -> None:
        target_group = await GroupRepository.get_group_by_id(db, group_id)
        ensure_exists(target_group, GroupNotFoundError(HTTP404.GROUP))

        has_students = await GroupRepository.has_active_students(db, group_id)
        has_assignments = await GroupRepository.has_active_teaching_assignments(
            db, group_id
        )

        if target_group.is_archived and target_group.archived_at is not None:
            logger.warning(
                "group_archive_denied",
                group_id=group_id,
                actor_user_id=current_user_id,
                denial_reason="group_is_already_archived",
            )

            raise GroupAlreadyArchivedError("Group is already archived")

        if has_students or has_assignments:
            logger.warning(
                "group_archive_denied",
                group_id=group_id,
                actor_user_id=current_user_id,
                denial_reason="active_students_or_teaching_assignments_reference_group",
            )

            raise GroupArchiveBlockedError(
                "Cannot archive a group with active students or teaching "
                "assignments; reassign or remove them first"
            )

        target_group.is_archived = True
        target_group.archived_at = datetime.now(UTC)

        await delete_cache(GroupCacheKey.group_detail_key_admin(group_id))

        await db.commit()

        logger.info(
            "group_archived",
            group_id=group_id,
            archived_by=current_user_id,
        )

    @staticmethod
    async def restore_group(
        db: AsyncSession, current_user_id: int, group_id: int
    ) -> None:
        target_group = await GroupRepository.get_group_by_id(db, group_id)
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

        await delete_cache(GroupCacheKey.group_detail_key_admin(group_id))

        await db.commit()

        logger.info(
            "group_restored",
            group_id=group_id,
            restored_by=current_user_id,
        )

    @staticmethod
    async def get_groups(
        db: AsyncSession,
        skip: int,
        limit: int,
        filters: SearchGroup,
        sort_by: str,
        order: str,
    ) -> PaginatedResponse:
        groups, total = await GroupRepository.get_groups(
            db,
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
    async def get_group_by_id(db: AsyncSession, group_id: int) -> GroupResponse:
        cache_key = GroupCacheKey.group_detail_key_admin(group_id)
        cached = await get_cache(cache_key)

        if cached is not None:
            raw = GroupCacheSchema.model_validate(cached)

            return GroupResponse.model_validate(raw.model_dump())

        group = await GroupRepository.get_group_by_id(db, group_id)
        ensure_exists(group, GroupNotFoundError(HTTP404.GROUP))

        raw = GroupCacheSchema.model_validate(group)
        await set_cache(cache_key, raw.model_dump(mode="json"), 900)

        return GroupResponse.model_validate(group)

    @staticmethod
    async def get_students(
        db: AsyncSession, group_id: int, skip: int, limit: int
    ) -> PaginatedResponse:
        await GroupService.get_group_by_id(db, group_id)

        students, total = await GroupRepository.get_students(db, group_id, skip, limit)

        return PaginatedResponse(
            items=students,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def add_student_to_group(
        db: AsyncSession, current_user_id: int, group_id: int, student_id: int
    ) -> None:
        group = await GroupRepository.get_group_by_id(db, group_id)
        ensure_exists(group, GroupNotFoundError(HTTP404.GROUP))

        student = await UserRepositoryBase.get_user_by_id(
            db, student_id, allowed_roles=frozenset({UserRole.STUDENT})
        )
        ensure_exists(student, UserNotFoundError(HTTP404.USER))

        previous_group_id = student.group_id

        if group.capacity is not None:
            await acquire_group_capacity_lock(db, group_id)
            current_count = await GroupRepository.count_active_students(db, group_id)

            if current_count >= group.capacity:
                logger.warning(
                    "group_capacity_exceeded",
                    group_id=group_id,
                    actor_user_id=current_user_id,
                    denial_reason="group_at_capacity",
                )

                raise GroupCapacityExceededError(
                    f"Group is at capacity ({group.capacity})"
                )

        student.group_id = group_id

        await db.commit()

        logger.info(
            "student_added_to_group",
            student_id=student_id,
            group_id=group_id,
            previous_group_id=previous_group_id,
            actor_user_id=current_user_id,
        )

    @staticmethod
    async def remove_student_from_group(
        db: AsyncSession, current_user_id: int, group_id: int, student_id: int
    ) -> None:
        student = await UserRepositoryBase.get_user_by_id(
            db, student_id, allowed_roles=frozenset({UserRole.STUDENT})
        )
        ensure_exists(student, UserNotFoundError(HTTP404.USER))

        student.group_id = None

        await db.commit()

        logger.info(
            "student_removed_from_group",
            student_id=student_id,
            group_id=group_id,
            actor_user_id=current_user_id,
        )
