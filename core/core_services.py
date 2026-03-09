from fastapi import HTTPException

from core.core_repositories import CoreRepository
from sqlalchemy.exc import IntegrityError
from src.models.core_models import StudentSubject, StudentGroup, TeacherGroup, TeacherSubject
from src.models.mark_model import Mark

MESSAGE_403 = "Accessing denied"


class CoreService:
    @staticmethod
    def is_admin(user):
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail=MESSAGE_403)
        

    @staticmethod
    def is_teacher(user):
        if user["role"] != "teacher":
            raise HTTPException(status_code=403, detail=MESSAGE_403)
        
    
    @staticmethod
    def does_have_access(user):
        if user["role"] not in ("director", "vice_director", "head_of_class"):
            raise HTTPException(status_code=403, detail=MESSAGE_403)
        
    
    @staticmethod
    def is_student(user, student_id):
        if user["id"] != student_id:
            raise HTTPException(status_code=403, detail=MESSAGE_403)
        

    @staticmethod
    def add(db, user, item, model):
        CoreService.is_admin(user)
        new_item = model(**item.model_dump())

        try:
            CoreRepository.add_item(db, new_item)

            db.commit()
            db.refresh(new_item)

            return new_item
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Duplicate values are not accepted")
        

    @staticmethod
    def delete(db, user, item_id):
        CoreService.is_admin(user)
        item = CoreRepository.get_item_by_id(db, item_id)

        if item is None:
            raise HTTPException(status_code=404, detail='Item not founf')

        CoreRepository.delete_item(db, item)

        db.commit()


    @staticmethod
    def update(db, user, item_id, student_subject_update_info_request):
        CoreService.is_admin(user)

        item = CoreRepository.get_item_by_id(db, item_id)

        if item is None:
            raise HTTPException(status_code=404, detail='Item not founf')
        
        for field, value in student_subject_update_info_request.model_dump(exclude_unset=True).items():
            setattr(item, field, value)

        db.commit()

        return item
    

    @staticmethod
    def get_student_subjects(db, user):
        CoreService.is_admin(user)

        return CoreRepository.get_items(db, StudentSubject)
    

    @staticmethod
    def get_student_groups(db, user):
        CoreService.is_admin(user)

        return CoreRepository.get_items(db, StudentGroup)
    
    @staticmethod
    def get_teacher_subjects(db, user):
        CoreService.is_admin(user)

        return CoreRepository.get_items(db, TeacherSubject)

    @staticmethod
    def get_teacher_groups(db, user):
        CoreService.is_admin(user)

        return CoreRepository.get_items(db, TeacherGroup)
    

    @staticmethod
    def get_teacher_groups(db, user):
        CoreService.is_teacher(user)

        return CoreRepository.get_items(db, Mark)