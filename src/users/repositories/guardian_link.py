from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.users.models.guardian_link import StudentGuardianLink
from src.utils.enums import GuardianPriority


class GuardianLinkRepository:
    @staticmethod
    def add_link(db: AsyncSession, link: StudentGuardianLink) -> None:
        db.add(link)

    @staticmethod
    async def get_link(
        db: AsyncSession, parent_id: int, student_id: int
    ) -> StudentGuardianLink | None:
        query = select(StudentGuardianLink).where(
            StudentGuardianLink.parent_id == parent_id,
            StudentGuardianLink.student_id == student_id,
        )
        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_link_by_priority(
        db: AsyncSession, student_id: int, priority: GuardianPriority
    ) -> StudentGuardianLink | None:
        query = select(StudentGuardianLink).where(
            StudentGuardianLink.student_id == student_id,
            StudentGuardianLink.priority == priority,
        )
        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def count_guardians_for_student(db: AsyncSession, student_id: int) -> int:
        query = select(func.count(StudentGuardianLink.parent_id)).where(
            StudentGuardianLink.student_id == student_id
        )
        result = await db.execute(query)

        return result.scalar()

    @staticmethod
    async def get_children_for_guardian(
        db: AsyncSession, guardian_id: int
    ) -> list[StudentGuardianLink]:
        query = (
            select(StudentGuardianLink)
            .options(joinedload(StudentGuardianLink.student))
            .where(StudentGuardianLink.parent_id == guardian_id)
        )
        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def guardian_has_access_to_student(
        db: AsyncSession, guardian_id: int, student_id: int
    ) -> bool:
        link = await GuardianLinkRepository.get_link(db, guardian_id, student_id)

        return link is not None
