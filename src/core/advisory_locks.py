import hashlib
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger

logger = get_logger(__name__)

NAMESPACE_STUDENT_PHONE = 9001
NAMESPACE_STUDENT_EMAIL = 9002
NAMESPACE_GROUP_CAPACITY = 9003

ADVISORY_LOCK_SQL = "SELECT pg_advisory_xact_lock(:ns, :key)"


def _compute_lock_key(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    unsigned = int.from_bytes(digest[:4], byteorder="big", signed=False)

    return unsigned - 2**32 if unsigned >= 2**31 else unsigned


async def acquire_student_contact_lock(
    session: AsyncSession,
    *,
    phone_number: str | None,
    email: str | None,
) -> None:
    if phone_number:
        normalized_phone = re.sub(r"[\s\-().]", "", phone_number).lower()
        key = _compute_lock_key(normalized_phone)

        logger.debug(
            "acquiring_advisory_lock",
            lock_type="student_phone",
            namespace=NAMESPACE_STUDENT_PHONE,
            key=key,
        )

        await session.execute(
            text(ADVISORY_LOCK_SQL),
            {"ns": NAMESPACE_STUDENT_PHONE, "key": key},
        )

        logger.debug(
            "advisory_lock_acquired",
            lock_type="student_phone",
            namespace=NAMESPACE_STUDENT_PHONE,
            key=key,
        )

    if email:
        normalized_email = email.strip().lower()
        key = _compute_lock_key(normalized_email)

        logger.debug(
            "acquiring_advisory_lock",
            lock_type="student_email",
            namespace=NAMESPACE_STUDENT_EMAIL,
            key=key,
        )

        await session.execute(
            text(ADVISORY_LOCK_SQL),
            {"ns": NAMESPACE_STUDENT_EMAIL, "key": key},
        )

        logger.debug(
            "advisory_lock_acquired",
            lock_type="student_email",
            namespace=NAMESPACE_STUDENT_EMAIL,
            key=key,
        )


async def acquire_group_capacity_lock(session: AsyncSession, group_id: int) -> None:
    key = _compute_lock_key(f"group:{group_id}")

    logger.debug(
        "acquiring_advisory_lock",
        lock_type="group_capacity",
        namespace=NAMESPACE_GROUP_CAPACITY,
        group_id=group_id,
        key=key,
    )

    await session.execute(
        text(ADVISORY_LOCK_SQL),
        {"ns": NAMESPACE_GROUP_CAPACITY, "key": key},
    )

    logger.debug(
        "advisory_lock_acquired",
        lock_type="group_capacity",
        namespace=NAMESPACE_GROUP_CAPACITY,
        group_id=group_id,
        key=key,
    )
