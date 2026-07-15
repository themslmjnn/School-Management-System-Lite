from sqlalchemy.ext.asyncio import AsyncSession

from src.academics.models import StudentSubjectEnrollment
from src.academics.repository import StudentSubjectEnrollmentRepository
from src.core.logging import get_logger
from src.subjects.repository import SubjectRepository
from src.users.repositories.users import UserRepositoryBase
from src.utils.constants import HTTP404
from src.utils.enums import UserRole
from src.utils.exceptions import (
    StudentAlreadyEnrolledError,
    StudentNotFoundError,
    StudentNotInGroupError,
    StudentSubjectEnrollmentNotFoundError,
    SubjectIsArchivedError,
    SubjectNotFoundError,
)
from src.utils.helpers import ensure_exists

logger = get_logger(__name__)


class StudentSubjectEnrollmentService:
    @staticmethod
    async def enroll_student(
        db: AsyncSession, current_user_id: int, student_id: int, subject_id: int
    ) -> StudentSubjectEnrollment:
        student = await UserRepositoryBase.get_user_by_id(
            db, student_id, allowed_roles=frozenset({UserRole.STUDENT})
        )
        ensure_exists(student, StudentNotFoundError(HTTP404.USER))

        if student.group_id is None:
            logger.warning(
                "student_enrollment_denied",
                student_id=student_id,
                subject_id=subject_id,
                actor_user_id=current_user_id,
                denial_reason="student_has_no_group",
            )
            raise StudentNotInGroupError(
                "Cannot enroll a student in a subject before they are "
                "assigned to a group"
            )

        subject = await SubjectRepository.get_subject_by_id(db, subject_id)
        ensure_exists(subject, SubjectNotFoundError(HTTP404.SUBJECT))

        if subject.is_archived:
            logger.warning(
                "student_enrollment_denied",
                student_id=student_id,
                subject_id=subject_id,
                actor_user_id=current_user_id,
                denial_reason="subject_is_archived",
            )
            raise SubjectIsArchivedError(
                "Cannot enroll a student in an archived subject"
            )

        existing = await StudentSubjectEnrollmentRepository.get_by_student_and_subject(
            db, student_id, subject_id
        )
        if existing is not None:
            raise StudentAlreadyEnrolledError(
                "This student is already enrolled in this subject"
            )

        enrollment = await StudentSubjectEnrollmentRepository.create_single(
            db, student_id, subject_id, student.group_id
        )
        await db.commit()
        await db.refresh(enrollment)

        logger.info(
            "student_enrolled_individually",
            student_id=student_id,
            subject_id=subject_id,
            group_id=student.group_id,
            enrolled_by=current_user_id,
        )
        return enrollment

    @staticmethod
    async def unenroll_student(
        db: AsyncSession, current_user_id: int, student_id: int, subject_id: int
    ) -> None:
        enrollment = (
            await StudentSubjectEnrollmentRepository.get_by_student_and_subject(
                db, student_id, subject_id
            )
        )
        ensure_exists(
            enrollment, StudentSubjectEnrollmentNotFoundError(HTTP404.SUBJECT)
        )

        await db.delete(enrollment)
        await db.commit()

        logger.info(
            "student_unenrolled",
            student_id=student_id,
            subject_id=subject_id,
            unenrolled_by=current_user_id,
        )

    @staticmethod
    async def get_enrolled_subjects(
        db: AsyncSession, student_id: int
    ) -> list[StudentSubjectEnrollment]:
        student = await UserRepositoryBase.get_user_by_id(
            db, student_id, allowed_roles=frozenset({UserRole.STUDENT})
        )
        ensure_exists(student, StudentNotFoundError(HTTP404.USER))

        return await StudentSubjectEnrollmentRepository.get_by_student(db, student_id)
