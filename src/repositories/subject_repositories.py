from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.subject_model import Subject

class SubjectRepository:
    @staticmethod
    def add_subject(db: Session, new_subject):
        db.add(new_subject)

    @staticmethod
    def remove_subject(db: Session, subject):
        db.delete(subject)


    @staticmethod
    def get_subject_by_id(db: Session, subject_id: int):
        query = (
            select(Subject)
            .filter(Subject.id == subject_id)
        )

        result = db.execute(query)

        return result.scalars().first()
    

    @staticmethod
    def get_subjects(db: Session):
        query = select(Subject)

        result = db.execute(query)

        return result.scalars().all()