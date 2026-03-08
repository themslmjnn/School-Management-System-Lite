from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError

from src.models.user_model import User
from src.repositories.user_repositories import UserRepository


MESSAGE_404 = "User not found"
MESSAGE_409 = "Duplicate values are not accepted"


class UserService:
    @staticmethod
    def register_user(db, new_user, bcrypt_context):
        user = User(
            username=new_user.username,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            date_of_birth=new_user.date_of_birth,
            address=new_user.address,
            email=new_user.email,
            phone_number=new_user.phone_number,
            password_hash=bcrypt_context.hash(new_user.password),
            role=new_user.role
        )

        try:
            UserRepository.register_user(db, user)

            db.commit()
            db.refresh(user)

            return user
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail=MESSAGE_409)
        

    @staticmethod
    def get_all_users(db):
        return UserRepository.get_all_users(db)
    

    @staticmethod
    def search_users(db, users_request):
        return UserRepository.search_users(db, users_request)
    

    @staticmethod
    def update_user_info(db, user_id, user_request):
        user = UserRepository.get_user_by_id(db, user_id)

        if user is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        for field, value in user_request.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        db.commit()

        return user
    

    @staticmethod
    def update_user_password(db, user_id, user_password_request, bcrypt_context):
        user = UserRepository.get_user_by_id(db, user_id)

        if user is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        if not bcrypt_context.verify(user_password_request.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid old password")
        
        user.password_hash = bcrypt_context.hash(user_password_request.new_password)

        db.commit()