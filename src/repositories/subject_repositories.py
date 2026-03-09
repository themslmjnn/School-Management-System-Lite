from sqlalchemy.orm import Session

class SubjectRepository:
    @staticmethod
    def delete_subject_by_id(db: Session, subject):
        db.delete(subject)