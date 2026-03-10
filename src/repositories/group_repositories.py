from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.group_model import Group

class GroupRepository:
    @staticmethod
    def add_group(db: Session, new_group):
        db.add(new_group)


    @staticmethod
    def delete_group(db: Session, group):
        db.delete(group)


    @staticmethod
    def get_group_by_id(db: Session, group_id):
        query = (
            select(Group)
            .filter(Group.id == group_id)
        )

        result = db.execute(query)

        return result.scalars().first()
    

    @staticmethod
    def get_groups(db: Session):
        query = select(Group)

        result = db.execute(query)

        return result.scalars().all()