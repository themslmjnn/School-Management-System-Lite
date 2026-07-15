from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.groups.models import Group
from src.groups.repository import GroupRepository
from src.groups.schemas import GroupCreate
from utils.exceptions import (
    handle_group_name_year_integrity_error,
    raise_unhandled_integrity_error,
)

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