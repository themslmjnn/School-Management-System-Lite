from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.academics.models.head_of_class_assignment import HeadOfClassAssignment


class HeadOfClassRepository:
    @staticmethod
    def add_head_of_class(
        db: AsyncSession, new_head_of_class: HeadOfClassAssignment
    ) -> None:
        db.add(new_head_of_class)

    @staticmethod
    async def get_by_group(
        db: AsyncSession, group_id: int
    ) -> list[HeadOfClassAssignment]:
        query = select(HeadOfClassAssignment).filter(
            HeadOfClassAssignment.group_id == group_id
        )

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession, assignment_id: int
    ) -> HeadOfClassAssignment | None:
        query = select(HeadOfClassAssignment).filter(
            HeadOfClassAssignment.id == assignment_id
        )

        result = await db.execute(query)

        return result.scalar_one_or_none()
