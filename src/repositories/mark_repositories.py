from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.mark_model import Mark


class MarkRepository:
    @staticmethod
    def put_mark(db: Session, new_mark):
        db.add(new_mark)


    @staticmethod
    def delete_mark(db: Session, mark):
        db.delete(mark)

    
    @staticmethod
    def get_mark_by_id(db: Session, mark_id):
        query = (
            select(Mark)
            .filter(Mark.id == mark_id)
        )

        result = db.execute(query)

        return result.scalars().first()
    

    @staticmethod
    def get_marks(db: Session):
        query = select(Mark)

        result = db.execute(query)

        return result.scalars().all()