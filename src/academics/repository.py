from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.academics.models import (
    HeadOfClassAssignment,
    StudentSubjectEnrollment,
    TeachingAssignment,
)


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


class StudentSubjectEnrollmentRepository:
    @staticmethod
    async def bulk_create_for_group_subject(
        db: AsyncSession, group_id: int, subject_id: int, student_ids: list[int]
    ) -> None:
        db.add_all(
            [
                StudentSubjectEnrollment(
                    student_id=student_id, subject_id=subject_id, group_id=group_id
                )
                for student_id in student_ids
            ]
        )

    @staticmethod
    async def get_by_student(
        db: AsyncSession, student_id: int
    ) -> list[StudentSubjectEnrollment]:
        query = select(StudentSubjectEnrollment).filter(
            StudentSubjectEnrollment.student_id == student_id
        )

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def get_by_group_and_subject(
        db: AsyncSession, group_id: int, subject_id: int
    ) -> list[StudentSubjectEnrollment]:
        query = select(StudentSubjectEnrollment).filter(
            StudentSubjectEnrollment.group_id == group_id,
            StudentSubjectEnrollment.subject_id == subject_id,
        )

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def get_by_student_and_subject(
        db: AsyncSession, student_id: int, subject_id: int
    ) -> "StudentSubjectEnrollment | None":
        result = await db.execute(
            select(StudentSubjectEnrollment).filter(
                StudentSubjectEnrollment.student_id == student_id,
                StudentSubjectEnrollment.subject_id == subject_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_single(
        db: AsyncSession, student_id: int, subject_id: int, group_id: int
    ) -> "StudentSubjectEnrollment":
        enrollment = StudentSubjectEnrollment(
            student_id=student_id, subject_id=subject_id, group_id=group_id
        )
        db.add(enrollment)
        return enrollment
