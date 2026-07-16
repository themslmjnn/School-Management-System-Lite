import asyncio

from src.core.logging import get_logger
from src.database import AsyncSessionLocal
from users.repositories.user import UserRepositoryBase

logger = get_logger(__name__)

DELETION_SWEEP_INTERVAL_SECONDS = 60 * 60 * 24


async def _run_deletion_sweep() -> None:
    async with AsyncSessionLocal() as db:
        try:
            user_ids_due = await UserRepositoryBase.get_user_ids_due_for_hard_deletion(
                db
            )
        except Exception as e:
            logger.error(
                "deletion_sweep_read_failed",
                error=str(e),
                exc_info=True,
            )

            return

    if not user_ids_due:
        logger.info(
            "deletion_sweep_completed",
            accounts_deleted=0,
            accounts_skipped=0,
        )
        return

    deleted_ids: list[int] = []
    skipped_ids: list[int] = []
    failed_ids: list[int] = []

    async with AsyncSessionLocal() as db:
        for user_id in user_ids_due:
            try:
                was_deleted = await UserRepositoryBase.delete_user_if_due(db, user_id)
                await db.commit()

                if was_deleted:
                    deleted_ids.append(user_id)
                else:
                    skipped_ids.append(user_id)

            except Exception as e:
                await db.rollback()
                failed_ids.append(user_id)

                logger.error(
                    "deletion_sweep_account_failed",
                    user_id=user_id,
                    error=str(e),
                    exc_info=True,
                )

    logger.info(
        "deletion_sweep_completed",
        accounts_deleted=len(deleted_ids),
        deleted_user_ids=deleted_ids,
        accounts_skipped=len(skipped_ids),
        skipped_user_ids=skipped_ids,
        accounts_failed=len(failed_ids),
        failed_user_ids=failed_ids,
    )


async def start_deletion_worker() -> None:
    logger.info("deletion_worker_started")

    while True:
        await _run_deletion_sweep()
        await asyncio.sleep(DELETION_SWEEP_INTERVAL_SECONDS)
