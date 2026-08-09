import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.caching import delete_cache
from src.core.logging import get_logger
from src.users.exceptions.constants import HTTP404
from src.users.exceptions.exceptions import (
    GuardianAlreadyPendingDeletionError,
    UserNotFoundError,
)
from src.users.repositories.user import UserRepositoryBase
from src.utils import email as email_sender
from src.utils.cache_keys import SessionCacheKey, UserCacheKey
from src.utils.enums import EmailType, UserRole, UserStatus
from src.utils.helpers import ensure_exists

logger = get_logger(__name__)

DELETION_GRACE_PERIOD_DAYS = 30


class UserServiceGuardian:
    @staticmethod
    async def create_guardian_self_deletion_request(
        session: AsyncSession,
        current_user_id: int,
    ) -> None:
        target_guardian = await UserRepositoryBase.get_user_by_id(
            session,
            current_user_id,
            load_session=True,
            allowed_roles=frozenset({UserRole.GUARDIAN}),
        )
        ensure_exists(target_guardian, UserNotFoundError(HTTP404.USER))

        if target_guardian.status == UserStatus.PENDING_DELETION:
            logger.warning(
                "guardian_self_deletion_request_denied",
                guardian_id=current_user_id,
                denial_reason="guardian_is_already_pending_deletion",
            )

            raise GuardianAlreadyPendingDeletionError(
                "Your account is already scheduled for deletion"
            )

        deletion_scheduled_for = datetime.now(UTC) + timedelta(
            days=DELETION_GRACE_PERIOD_DAYS
        )

        target_guardian.status = UserStatus.PENDING_DELETION
        target_guardian.is_active = False
        target_guardian.deletion_scheduled_for = deletion_scheduled_for

        target_guardian.session.access_token_version += 1
        target_guardian.session.refresh_token_hash = None
        target_guardian.session.refresh_token_family = None
        target_guardian.session.refresh_token_expires_at = None

        await session.commit()

        asyncio.create_task(
            email_sender.send_safe(
                email_sender.send_account_deletion_email(target_guardian.email),
                email_type=EmailType.ACCOUNT_DELETION,
            )
        )

        await delete_cache(
            SessionCacheKey.access_token_version_key(current_user_id),
            UserCacheKey.user_detail_key_admin(current_user_id),
            UserCacheKey.user_detail_key_self(current_user_id),
        )

        logger.info(
            "guardian_self_deletion_scheduled",
            user_id=current_user_id,
            deletion_scheduled_for=deletion_scheduled_for.isoformat(),
        )
