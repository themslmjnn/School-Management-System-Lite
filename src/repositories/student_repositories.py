from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models.student_model import Student
from src.models.association_models import StudentGroup, StudentSubject


class StudentRepository:
    @staticmethod
    def register_student(db: Session, new_student):
        db.add(new_student)

    @staticmethod
    def get_students(db: Session):
        query = select(Student).options(selectinload(Student.user))

        result = db.execute(query)

        return result.scalars().all()

    @staticmethod
    def get_student_by_id(db: Session, student_id):
        query = select(Student).filter(Student.id == student_id)

        result = db.execute(query)

        return result.scalars().first()

    @staticmethod
    def enroll_student_in_subject(db: Session, new_enrollment):
        db.add(new_enrollment)

    @staticmethod
    def get_student_subject_by_id(db: Session, enrollment_id):
        query = select(StudentSubject).filter(StudentSubject.id == enrollment_id)

        result = db.execute(query)

        return result.scalars().first()

    @staticmethod
    def get_students_subjects(db: Session):
        query = select(StudentSubject)

        result = db.execute(query)

        return result.scalars().all()

    @staticmethod
    def add_student_to_group(db: Session, new_enrollment):
        db.add(new_enrollment)

    @staticmethod
    def get_student_group_by_id(db: Session, enrollment_id):
        query = select(StudentGroup).filter(StudentGroup.id == enrollment_id)

        result = db.execute(query)

        return result.scalars().first()

    @staticmethod
    def get_students_groups(db: Session):
        query = select(StudentGroup)

        result = db.execute(query)

        return result.scalars().all()
