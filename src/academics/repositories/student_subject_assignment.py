from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.academics.models.student_subject_enrollment import StudentSubjectEnrollment


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
