from src.models.subject_model import Subject
from core.core_repositories import CoreRepository
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from src.models.group_model import Group
from src.repositories.subject_repositories import SubjectRepository
from core.core_services import CoreService
class GroupService:
    @staticmethod
    def add_group_admin(db, user, group_request):
        CoreService.is_admin(user)
        new_group = Group(**group_request.model_dump())

        try:
            CoreRepository.add_item(db, new_group)

            db.commit()
            db.refresh(new_group)

            return new_group
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Group already exists")
        
    @staticmethod
    def delete_group_admin(db, user, group_id):
        CoreService.is_admin(user)
        group = CoreRepository.get_item_by_id(db, group_id, Group)

        if group is None:
            raise HTTPException(status_code=404, detail="Group not found")
        
        SubjectRepository.delete_subject_by_id(db, group)

        db.commit()


    @staticmethod
    def update_group_info_admin(db, user, group_id, group_update_info_request):
        CoreService.is_admin(user)
        group = CoreRepository.get_item_by_id(db, group_id, Group)

        if group is None:
            raise HTTPException(status_code=404, detail="Group not found")
        
        for field, value in group_update_info_request.model_dump(exclude_unset=True).items():
            setattr(group, field, value)
        
        db.commit()

        return group
    

    @staticmethod
    def get_groups_admin(db, user):
        CoreService.is_admin(user)
        return CoreRepository.get_items(db, Group)