import hashlib

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

ADVISORY_LOCK_NAMESPACE_STUDENT_PHONE = 9001
ADVISORY_LOCK_NAMESPACE_STUDENT_EMAIL = 9002


def compute_contact_lock_key(normalized_value: str) -> int:
    digest = hashlib.sha256(normalized_value.encode("utf-8")).digest()
    unsigned_32 = int.from_bytes(digest[:4], byteorder="big", signed=False)

    return unsigned_32 - 2**32 if unsigned_32 >= 2**31 else unsigned_32


async def acquire_student_contact_lock(
    db: AsyncSession,
    *,
    phone_number: str | None,
    email: str | None,
) -> None:
    if phone_number:
        key = compute_contact_lock_key(phone_number)

        await db.execute(
            text("SELECT pg_advisory_xact_lock(:ns, :key)"),
            {
                "ns": ADVISORY_LOCK_NAMESPACE_STUDENT_PHONE,
                "key": key,
            },
        )

    if email:
        key = compute_contact_lock_key(email.strip().lower())

        await db.execute(
            text("SELECT pg_advisory_xact_lock(:ns, :key)"),
            {
                "ns": ADVISORY_LOCK_NAMESPACE_STUDENT_EMAIL,
                "key": key,
            },
        )
