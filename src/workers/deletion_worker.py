import asyncio

from src.core.logging import get_logger
from src.database import AsyncSessionLocal
from src.users.repositories.users import UserRepositoryBase

logger = get_logger(__name__)

DELETION_SWEEP_INTERVAL_SECONDS = 60 * 60 * 24


async def _run_deletion_sweep() -> None:
    async with AsyncSessionLocal() as db:
        try:
            accounts_due = await UserRepositoryBase.get_users_due_for_hard_deletion(db)

            if not accounts_due:
                logger.info(
                    "deletion_sweep_completed",
                    accounts_deleted=0,
                )
                return

            deleted_ids = []

            for user in accounts_due:
                deleted_ids.append(user.id)

                await UserRepositoryBase.delete_user(user)

            await db.commit()

            logger.info(
                "deletion_sweep_completed",
                accounts_deleted=len(deleted_ids),
                deleted_user_ids=deleted_ids,
            )

        except Exception as e:
            await db.rollback()

            logger.error(
                "deletion_sweep_failed",
                error=str(e),
                exc_info=True,
            )


async def start_deletion_worker() -> None:
    logger.info("deletion_worker_started")

    while True:
        await _run_deletion_sweep()
        await asyncio.sleep(DELETION_SWEEP_INTERVAL_SECONDS)
