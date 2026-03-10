from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.user_model import User


class UserRepository:
    @staticmethod
    def register_user(db: Session, new_user):
        db.add(new_user)


    @staticmethod
    def get_users_admin(db: Session):
        query = select(User)

        result = db.execute(query)

        return result.scalars().all()
    

    @staticmethod
    def get_users_public(db: Session):
        query = (
            select(
                User.first_name, 
                User.last_name, 
                User.date_of_birth, 
                User.address, 
                User.phone_number, 
                User.role, 
                User.is_active)
        )

        result = db.execute(query)

        return result.scalars().all()
    

    @staticmethod
    def get_user_by_id(db: Session, user_id):
        query = (
            select(User)
            .filter(User.id == user_id)
        )

        result = db.execute(query)

        return result.scalars().first()


    @staticmethod
    def search_users(db: Session, users_request):
        query = select(User)

        if users_request.username:
            query = query.filter(User.username.ilike('%' + users_request.username + '%'))

        if users_request.first_name:
            query = query.filter(User.first_name.ilike('%' + users_request.first_name + '%'))

        if users_request.last_name:
            query = query.filter(User.last_name.ilike('%' + users_request.last_name + '%'))

        if users_request.date_of_birth:
            query = query.filter(User.date_of_birth == users_request.date_of_birth)

        if users_request.role:
            query = query.filter(User.role == users_request.role)

        if users_request.is_active is not None:
            query = query.filter(User.is_active == users_request.is_active)

        result = db.execute(query)

        return result.scalars().all()