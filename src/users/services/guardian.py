import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import delete_cache
from src.core.logging import get_logger
from src.users.repositories.users import UserRepositoryBase
from src.utils import email as email_sender
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.constants import HTTP404
from src.utils.enums import EmailType, UserRole, UserStatus
from src.utils.exceptions import UserAlreadyPendingDeletionError, UserNotFoundError
from src.utils.helpers import ensure_exists

logger = get_logger(__name__)

DELETION_GRACE_PERIOD_DAYS = 30


class UserServiceGuardian:
    @staticmethod
    async def create_guardian_self_deletion_request(
        db: AsyncSession,
        current_user_id: int,
    ) -> None:
        target_user = await UserRepositoryBase.get_user_by_id(
            db,
            current_user_id,
            load_session=True,
            allowed_roles=frozenset({UserRole.GUARDIAN}),
        )
        ensure_exists(target_user, UserNotFoundError(HTTP404.USER))

        if target_user.status == UserStatus.PENDING_DELETION:
            raise UserAlreadyPendingDeletionError(
                "Your account is already scheduled for deletion"
            )

        deletion_scheduled_for = datetime.now(UTC) + timedelta(
            days=DELETION_GRACE_PERIOD_DAYS
        )

        target_user.status = UserStatus.PENDING_DELETION
        target_user.is_active = False
        target_user.deletion_scheduled_for = deletion_scheduled_for

        target_user.session.access_token_version += 1
        target_user.session.refresh_token_hash = None
        target_user.session.refresh_token_family = None
        target_user.session.refresh_token_expires_at = None

        await db.commit()

        asyncio.create_task(
            email_sender.send_safe(
                email_sender.send_cancel_parent_deletion_email(target_user.email),
                email_type=EmailType.CANCEL_ACCOUNT_DELETION,
            )
        )

        await delete_cache(
            SessionCacheKey.access_token_version_key(current_user_id),
            UserCacheKey.user_detail_key_admin(current_user_id),
        )

        logger.info(
            "guardian_self_deletion_scheduled",
            user_id=current_user_id,
            deletion_scheduled_for=deletion_scheduled_for.isoformat(),
        )
