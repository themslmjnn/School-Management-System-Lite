from fastapi import HTTPException

from src.repositories.user_repositories import UserRepository
from utils.helpers import require_admin, require_director, ensure_exists, update_object, verify_password, hash_password, require_user


MESSAGE_404 = "User not found"


class UserService:
    @staticmethod
    def get_users(db, user):
        try:
            require_admin(user)
            result = UserRepository.get_users_admin(db)
            
        except HTTPException:
            require_director(user)
            result = UserRepository.get_users_public(db)
    
        return result
    

    @staticmethod
    def search_users(db, user, users_request):
        try:
            require_admin(user)
            
        except HTTPException:
            require_director(user)

        return UserRepository.search_users(db, users_request)
    

    @staticmethod
    def update_user_info(db, user, user_id, user_request):
        require_admin(user)

        user = UserRepository.get_user_by_id(db, user_id)

        ensure_exists(user, MESSAGE_404)

        update_object(user, user_request)

        db.commit()

        return user
    

    @staticmethod
    def update_user_password(db, user, user_id, user_password_request, bcrypt_context):
        try:
            require_admin(user)

        except HTTPException:
            require_user(user, user_id)

        user = UserRepository.get_user_by_id(db, user_id)

        ensure_exists(user, MESSAGE_404)
        
        verify_password(user_password_request.old_password, user.password_hash, bcrypt_context)
        
        user.password_hash = hash_password(user_password_request.new_password, bcrypt_context)

        db.commit()