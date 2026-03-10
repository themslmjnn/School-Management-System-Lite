from fastapi import HTTPException

from src.models.user_model import User
from src.repositories.user_repositories import UserRepository
from utils.helpers import require_admin, require_director, require_existence, update_object, verify_password, hash_password


MESSAGE_403 = "Accessing denied"
MESSAGE_404 = "User not found"


class UserService:
    @staticmethod
    def get_users(db, user):
        if require_admin(user) is None:
            return UserRepository.get_users_admin(db)
        elif require_director(user) is None:
            return UserRepository.get_users_public(db)
    

    @staticmethod
    def search_users(db, user, users_request):
        try:
            require_admin(user)

        finally:
            require_director(user)

        return UserRepository.search_users(db, users_request)
    

    @staticmethod
    def update_user_info(db, user, user_id, user_request):
        require_admin(user)

        user = UserRepository.get_user_by_id(db, user_id)

        require_existence(user, MESSAGE_404)

        update_object(user, user_request)

        db.commit()

        return user
    

    @staticmethod
    def update_user_password(db, user, user_id, user_password_request, bcrypt_context):
        try:
            require_admin(user)

        finally:
            require_director(user)

        user = UserRepository.get_user_by_id(db, user_id, User)

        require_existence(user, MESSAGE_404)
        
        verify_password(user, user_password_request, bcrypt_context)
        
        user.password_hash = hash_password(user_password_request, bcrypt_context)

        db.commit()