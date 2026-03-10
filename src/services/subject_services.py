from src.models.subject_model import Subject

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from src.models.subject_model import Subject
from src.repositories.subject_repositories import SubjectRepository
from utils.helpers import require_admin, require_existence, update_object, require_director

MESSAGE_404 = "Subject not found"

class SubjectService:
    @staticmethod
    def add_subject(db, user, subject_request):
        require_admin(user)

        subject = Subject(**subject_request.model_dump())

        try:
            SubjectRepository.add_subject(db, subject)

            db.commit()
            db.refresh(subject)

            return subject
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Subject already exists")
        

    @staticmethod
    def remove_subject(db, user, subject_id):
        require_admin(user)

        subject = SubjectRepository.get_subject_by_id(db, subject_id)

        require_existence(subject, MESSAGE_404)
        
        SubjectRepository.remove_subject(db, subject)

        db.commit()


    @staticmethod
    def update_subject_info(db, user, subject_id, subject_update_info_request):
        require_admin(user)

        subject = SubjectRepository.get_subject_by_id(db, subject_id)

        require_existence(subject, MESSAGE_404)

        update_object(subject, subject_update_info_request)

        db.commit()

        return subject
    

    @staticmethod
    def get_subjects(db, user):
        try:
            require_admin(user)

        finally:
            require_director(user)

        return SubjectRepository.get_subjects(db)