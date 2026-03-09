from sqlalchemy import select
from sqlalchemy.orm import Session


class CoreRepository:
    @staticmethod
    def add_item(db: Session, new_item):
        db.add(new_item)
    

    @staticmethod
    def get_items(db: Session, model):
        query = select(model)

        result = db.execute(query)

        return result.scalars().all()
    

    @staticmethod
    def get_item_by_id(db: Session, item_id: int, model):
        query = (
            select(model)
            .filter(model.id == item_id)
        )

        result = db.execute(query)

        return result.scalars().first()
    

    @staticmethod
    def delete_item(db: Session, item):
        db.delete(item)