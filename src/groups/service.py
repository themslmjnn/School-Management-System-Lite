from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.groups.models import Group
from src.groups.repository import GroupRepository
from src.groups.schemas import GroupCreate, GroupUpdate
from utils.constants import HTTP404
from utils.exceptions import (
    GroupArchiveBlockedError,
    GroupNotFoundError,
    handle_group_name_year_integrity_error,
    raise_unhandled_integrity_error,
)
from utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)


class GroupService:
    @staticmethod
    async def create_group(
        db: AsyncSession, current_user_id: int, request: GroupCreate
    ) -> Group:
        try:
            new_group = Group(**request.model_dump())
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
        db: AsyncSession, current_user_id: int, group_id: int, request: GroupUpdate
    ) -> Group:
        group = await GroupRepository.get_group_by_id(db, group_id)
        ensure_exists(group, GroupNotFoundError(HTTP404.GROUP))

        try:
            update_object(group, request)

            await db.commit()
            await db.refresh(group)

            logger.info(
                "group_updated",
                group_id=group_id,
                updated_by=current_user_id,
            )

            return group

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
        group = await GroupRepository.get_group_by_id(db, group_id)
        ensure_exists(group, GroupNotFoundError(HTTP404.GROUP))

        has_students = await GroupRepository.has_active_students(db, group_id)
        has_assignments = await GroupRepository.has_active_teaching_assignments(
            db, group_id
        )
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

        group.is_archived = True
        group.archived_at = datetime.now(UTC)

        await db.commit()

        logger.info(
            "group_archived",
            group_id=group_id,
            archived_by=current_user_id,
        )
