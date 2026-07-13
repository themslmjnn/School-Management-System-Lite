import asyncio

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import delete_cache
from src.core.logging import get_logger
from src.users.models.users import User
from src.users.repositories.users import UserRepositoryBase
from src.users.schemas.users import UpdateMeProfile
from src.utils import email as email_sender
from src.utils.cache_keys import UserCacheKey
from src.utils.constants import HTTP404
from src.utils.enums import UserRole
from src.utils.exceptions import (
    ProfileFieldsNotEditableForRoleError,
    UserNotFoundError,
    handle_non_student_unique_contact_error,
    raise_unhandled_integrity_error,
)
from src.utils.helpers import ensure_exists, update_object

logger = get_logger(__name__)

PROFILE_EDITABLE_ROLES = frozenset({UserRole.SYSTEM_ADMIN, UserRole.GUARDIAN})


class UserServiceSelf:
    @staticmethod
    async def update_me_profile(
        db: AsyncSession,
        current_user_id: int,
        update_request: UpdateMeProfile,
    ) -> User:
        current_user = await UserRepositoryBase.get_user_by_id(db, current_user_id)
        ensure_exists(current_user, UserNotFoundError(HTTP404.USER))

        if current_user.role not in PROFILE_EDITABLE_ROLES:
            logger.warning(
                "profile_update_denied",
                target_user_id=current_user_id,
                target_role=current_user.role.value,
                denial_reason="role_not_permitted_to_edit_profile_fields",
            )
            raise ProfileFieldsNotEditableForRoleError(
                "Your role does not permit editing profile fields directly. "
                "Contact a system administrator for changes."
            )

        try:
            update_object(current_user, update_request)

            await db.commit()
            await db.refresh(current_user)

            asyncio.create_task(
                email_sender.send_safe(
                    email_sender.send_account_info_updated_email(current_user.email),
                    email_type="updating_account",
                )
            )

            await delete_cache(UserCacheKey.user_detail_key_self(current_user_id))

            logger.info(
                "user_profile_updated",
                target_user_id=current_user_id,
                method="self_update",
            )

            return current_user

        except IntegrityError as e:
            await db.rollback()

            logger.error(
                "profile_update_failed",
                target_user_id=current_user_id,
                reason=str(e.orig),
            )
            handle_non_student_unique_contact_error(e)
            raise_unhandled_integrity_error(e)
