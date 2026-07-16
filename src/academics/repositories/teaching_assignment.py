from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.academics.models.teaching_assignment import TeachingAssignment


class TeachingAssignmentRepository:
    @staticmethod
    def add_assignment(db: AsyncSession, new_assignment: TeachingAssignment) -> None:
        db.add(new_assignment)

    @staticmethod
    async def get_assignment_by_id(
        db: AsyncSession, assignment_id: int
    ) -> TeachingAssignment | None:
        query = select(TeachingAssignment).filter(
            TeachingAssignment.id == assignment_id
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_assignment_by_group(
        db: AsyncSession, group_id: int
    ) -> list[TeachingAssignment]:
        query = select(TeachingAssignment).filter(
            TeachingAssignment.group_id == group_id
        )

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def get_assignment_by_teacher(
        db: AsyncSession, teacher_id: int
    ) -> list[TeachingAssignment]:
        query = select(TeachingAssignment).filter(
            TeachingAssignment.teacher_id == teacher_id
        )

        result = await db.execute(query)

        return list(result.scalars().all())
