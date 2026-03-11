from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models.teacher_model import Teacher
from src.models.user_model import User
from src.models.association_models import TeacherSubject, TeacherGroup


class TeacherRepository:
    @staticmethod
    def register_teacher(db: Session, new_teacher):
        db.add(new_teacher)


    @staticmethod
    def get_teachers(db: Session):
        query = (
            select(Teacher)
            .options(selectinload(Teacher.user))
        )

        result = db.execute(query)

        return result.scalars().all()
    

    # @staticmethod
    # def get_teachers_public(db: Session):
    #     query = (
    #         select(
    #             User.first_name, 
    #             User.last_name, 
    #             User.date_of_birth, 
    #             User.address,
    #             User.phone_number,
    #             User.role,
    #             User.is_active,
    #             Teacher.hired_at,
    #             Teacher.status
    #         )
    #         .options(selectinload(Teacher.user))
    #     )

    #     result = db.execute(query)

    #     return result.scalars().all()
    

    @staticmethod
    def get_teacher_by_id(db: Session, teacher_id):
        query = (
            select(Teacher)
            .filter(Teacher.id == teacher_id)
        )

        result = db.execute(query)

        return result.scalars().first()
    

    @staticmethod
    def assign_teacher_to_subject(db: Session, new_assingment):
        db.add(new_assingment)


    @staticmethod
    def get_teacher_subject_by_id(db: Session, assignment_id):
        query = (
            select(TeacherSubject)
            .filter(TeacherSubject.id == assignment_id)
        )

        result = db.execute(query)

        return result.scalars().first()
    

    @staticmethod
    def get_teachers_subjects(db: Session):
        query = select(TeacherSubject)

        result = db.execute(query)

        return result.scalars().all()
    

    @staticmethod
    def assign_head_of_class(db: Session, new_assigment):
        db.add(new_assigment)


    @staticmethod
    def get_teacher_group_by_id(db: Session, assignment_id):
        query = (
            select(TeacherGroup)
            .filter(TeacherGroup.id == assignment_id)
        )

        result = db.execute(query)

        return result.scalars().first()
    
    
    @staticmethod
    def get_teachers_groups(db: Session):
        query = select(TeacherGroup)

        result = db.execute(query)

        return result.scalars().all()