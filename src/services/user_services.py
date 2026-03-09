from fastapi import HTTPException

from src.models.user_model import User
from src.repositories.user_repositories import UserRepository
from core.core_repositories import CoreRepository
from core.core_services import CoreService


MESSAGE_403 = "Accessing denied"
MESSAGE_404 = "User not found"


class UserService:
    @staticmethod
    def get_users_admin(db, user):
        CoreService.is_admin(user)
        
        return CoreRepository.get_items(db, User)
    

    @staticmethod
    def search_users_admin(db, user, users_request):
        CoreService.is_admin(user)

        return UserRepository.search_users(db, users_request)
    

    @staticmethod
    def get_users_general(db, user):
        CoreService.does_have_access(user)
        
        return CoreRepository.get_items(db, User)
    

    @staticmethod
    def search_users_general(db, user, users_request):
        CoreService.does_have_access(user)

        return UserRepository.search_users(db, users_request)
    

    @staticmethod
    def update_user_info(db, user, user_id, user_request):
        CoreService.is_admin(user)

        user = CoreRepository.get_item_by_id(db, user_id, User)

        if user is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        for field, value in user_request.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        db.commit()

        return user
    

    @staticmethod
    def update_user_password(db, user, user_id, user_password_request, bcrypt_context):
        if user["role"] != "admin" and user["id"] != user_id:
            raise HTTPException(status_code=403, detail=MESSAGE_403)

        user = CoreRepository.get_item_by_id(db, user_id, User)

        if user is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        if not bcrypt_context.verify(user_password_request.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid old password")
        
        user.password_hash = bcrypt_context.hash(user_password_request.new_password)

        db.commit()