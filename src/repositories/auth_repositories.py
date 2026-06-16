from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User


class AuthRepository:
    @staticmethod
    def get_user_by_username(db: Session, username: str):
        query = (
            select(User)
            .filter(User.username == username)
        )

        result = db.execute(query)

        return result.scalars().first()