from src.models.subject_model import Subject

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from src.models.subject_model import Subject
from src.repositories.subject_repositories import SubjectRepository

class SubjectService:
    @staticmethod
    def add_subject_admin(db, user, subject_request):
        CoreService.is_admin(user)
        new_subject = Subject(**subject_request.model_dump())

        try:
            CoreRepository.add_item(db, new_subject)

            db.commit()
            db.refresh(new_subject)

            return new_subject
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Subject already exists")
        
    @staticmethod
    def delete_subject_admin(db, user, subject_id):
        CoreService.is_admin(user)
        subject = CoreRepository.get_item_by_id(db, subject_id, Subject)

        if subject is None:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        SubjectRepository.delete_subject_by_id(db, subject)

        db.commit()


    @staticmethod
    def update_subject_info_admin(db, user, subject_id, subject_update_info_request):
        CoreService.is_admin(user)
        subject = CoreRepository.get_item_by_id(db, subject_id, Subject)

        if subject is None:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        for field, value in subject_update_info_request.model_dump(exclude_unset=True).items():
            setattr(subject, field, value)
        
        db.commit()

        return subject
    

    @staticmethod
    def get_subjects_admin(db, user):
        CoreService.is_admin(user)
        return CoreRepository.get_items(db, Subject)