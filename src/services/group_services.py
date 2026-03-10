from src.models.subject_model import Subject

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from src.models.group_model import Group
from src.repositories.group_repositories import GroupRepository

from utils.helpers import require_admin, require_director, require_existence, update_object

MESSAGE_404 = "Group not found"

class GroupService:
    @staticmethod
    def add_group(db, user, group_request):
        require_admin(user)

        group = Group(**group_request.model_dump())

        try:
            GroupRepository.add_group(db, group)

            db.commit()
            db.refresh(group)

            return group
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Group already exists")
        

    @staticmethod
    def delete_group(db, user, group_id):
        require_admin(user)
        
        group = GroupRepository.get_group_by_id(db, group_id)

        require_existence(group, MESSAGE_404)

        GroupRepository.delete_group(db, group)

        db.commit()


    @staticmethod
    def update_group_info(db, user, group_id, group_update_info_request):
        require_admin(user)

        group = GroupRepository.get_group_by_id(db, group_id)

        require_existence(group, MESSAGE_404)

        update_object(group, group_update_info_request)
        
        db.commit()

        return group
    

    @staticmethod
    def get_groups(db, user):
        try:
            require_admin(user)

        finally:
            require_director(user)

        return GroupRepository.get_groups(db)