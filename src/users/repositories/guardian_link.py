from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models.guardian_link import StudentGuardianLink
from src.utils.enums import GuardianPriority


class GuardianLinkRepositoryAdmin:
    @staticmethod
    def add_link(db: AsyncSession, link: StudentGuardianLink) -> None:
        db.add(link)

    @staticmethod
    async def get_guardian_link(
        db: AsyncSession, parent_id: int, student_id: int
    ) -> StudentGuardianLink | None:
        query = select(StudentGuardianLink).where(
            StudentGuardianLink.guardian_id == parent_id,
            StudentGuardianLink.student_id == student_id,
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_guardian_link_by_priority(
        db: AsyncSession, student_id: int, priority: GuardianPriority
    ) -> StudentGuardianLink | None:
        query = select(StudentGuardianLink).where(
            StudentGuardianLink.student_id == student_id,
            StudentGuardianLink.priority == priority,
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()


class GuardianLinkRepositoryShared:
    @staticmethod
    async def get_children_for_guardian(
        db: AsyncSession, guardian_id: int
    ) -> list[StudentGuardianLink]:
        query = (
            select(StudentGuardianLink)
            .options(joinedload(StudentGuardianLink.student))
            .where(StudentGuardianLink.guardian_id == guardian_id)
        )

        result = await db.execute(query)

        return list(result.scalars().all())
