from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.student_model import Student
from src.models.user_model import User

class StudentRepository:
    @staticmethod
    def add(db: Session, new_student):
        db.add(new_student)
    

    @staticmethod
    def get_users(db: Session):
        query = select(Student).join(Student.user)

        result = db.execute(query)

        return result.scalars().all()
    
    @staticmethod
    def get_student_by_id(db: Session, student_id: int):
        query = (
            select(Student)
            .filter(Student.id == student_id)
        )

        result = db.execute(query)

        return result.scalars().first()