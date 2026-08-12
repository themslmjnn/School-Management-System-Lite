from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from academics.models.head_of_class_assignment import HeadOfClassAssignment
from src.guardian_links.models import StudentGuardianLink
from src.users.models.user import User
from src.utils.enums import GuardianPriority


class GuardianLinkRepository:
    @staticmethod
    async def get_link_by_id(
        session: AsyncSession,
        link_id: int,
    ) -> StudentGuardianLink | None:
        query = (
            select(StudentGuardianLink)
            .options(
                joinedload(StudentGuardianLink.guardian),
                joinedload(StudentGuardianLink.student).joinedload(User.group),
            )
            .where(StudentGuardianLink.id == link_id)
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_guardian_link(
        session: AsyncSession, guardian_id: int, student_id: int
    ) -> StudentGuardianLink | None:
        query = select(StudentGuardianLink).where(
            StudentGuardianLink.guardian_id == guardian_id,
            StudentGuardianLink.student_id == student_id,
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_guardian_link_by_priority(
        session: AsyncSession,
        student_id: int,
        priority: GuardianPriority,
    ) -> StudentGuardianLink | None:
        query = select(StudentGuardianLink).where(
            StudentGuardianLink.student_id == student_id,
            StudentGuardianLink.priority == priority,
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_links(
        session: AsyncSession,
        skip: int,
        limit: int,
    ) -> tuple[list[StudentGuardianLink], int]:
        count_query = select(func.count(StudentGuardianLink.id))
        total = (await session.execute(count_query)).scalar()

        query = (
            select(StudentGuardianLink)
            .options(
                joinedload(StudentGuardianLink.guardian),
                joinedload(StudentGuardianLink.student).joinedload(User.group),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(query)

        return list(result.scalars().all()), total

    @staticmethod
    async def get_links_for_head_of_class(
        db: AsyncSession,
        teacher_id: int,
    ) -> list[StudentGuardianLink]:
        query = (
            select(StudentGuardianLink)
            .options(
                joinedload(StudentGuardianLink.guardian),
                joinedload(StudentGuardianLink.student).joinedload(User.group),
            )
            .join(
                User,
                User.id == StudentGuardianLink.student_id,
            )
            .join(
                HeadOfClassAssignment,
                HeadOfClassAssignment.group_id == User.group_id,
            )
            .where(
                HeadOfClassAssignment.teacher_id == teacher_id,
                User.group_id.is_not(None),
            )
            .distinct()
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_link_for_head_of_class_by_id(
        db: AsyncSession,
        teacher_id: int,
        link_id: int,
    ) -> StudentGuardianLink | None:
        from src.academics.models import HeadOfClassAssignment

        query = (
            select(StudentGuardianLink)
            .options(
                joinedload(StudentGuardianLink.guardian),
                joinedload(StudentGuardianLink.student).joinedload(User.group),
            )
            .join(
                User,
                User.id == StudentGuardianLink.student_id,
            )
            .join(
                HeadOfClassAssignment,
                HeadOfClassAssignment.group_id == User.group_id,
            )
            .where(
                StudentGuardianLink.id == link_id,
                HeadOfClassAssignment.teacher_id == teacher_id,
                User.group_id.is_not(None),
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_links_for_student(
        db: AsyncSession,
        student_id: int,
    ) -> list[StudentGuardianLink]:
        query = (
            select(StudentGuardianLink)
            .options(joinedload(StudentGuardianLink.guardian))
            .where(StudentGuardianLink.student_id == student_id)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_link_for_student_by_id(
        db: AsyncSession,
        student_id: int,
        link_id: int,
    ) -> StudentGuardianLink | None:
        query = (
            select(StudentGuardianLink)
            .options(joinedload(StudentGuardianLink.guardian))
            .where(
                StudentGuardianLink.id == link_id,
                StudentGuardianLink.student_id == student_id,
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()