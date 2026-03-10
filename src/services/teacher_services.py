from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError

from src.models.user_model import User
from src.models.teacher_model import Teacher, TeacherStatus
from src.models.association_models import TeacherSubject, TeacherGroup, TeacherSubjectStatus
from src.repositories.teacher_repositories import TeacherRepository
from src.repositories.user_repositories import UserRepository
from utils.helpers import require_admin, require_director, require_existence, update_object


MESSAGE_404_1 = "Teacher not found"
MESSAGE_404_2 = "Assignment not found"
MESSAGE_409 = "Assignment already exists"


class TeacherService:
    @staticmethod
    def register_teacher(db, user, teacher_request, bcrypt_context):

        require_admin(user)

        try:
            user_data = teacher_request.teacher_primary_data

            user = User(
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                date_of_birth=user_data.date_of_birth,
                address=user_data.address,
                email=user_data.email,
                phone_number=user_data.phone_number,
                password_hash=bcrypt_context.hash(user_data.password),
                role="teacher"
            )

            UserRepository.register_user(db, user)

            db.flush()

            teacher = Teacher(primary_info_id=user.id, **teacher_request.teacher.model_dump())

            TeacherRepository.register_teacher(db, teacher)

            db.commit()
            db.refresh(teacher)

            return {"user": user, "teacher": teacher}
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Teacher already exists")
        

    @staticmethod
    def get_teachers(db, user):
        if require_admin(user) is None:
            teachers = TeacherRepository.get_teachers_admin(db)
        elif require_director(user) is None:
            teachers = TeacherRepository.get_teachers_public(db)

        return [
            {"user": teacher.user, "teacher": teacher}
            for teacher in teachers
        ]
    

    @staticmethod
    def update_teacher_info(db, user, teacher_id, teacher_update_info_request):
        require_admin(user)

        teacher = TeacherRepository.get_teacher_by_id(db, teacher_id)

        require_existence(teacher, MESSAGE_404_1)
        
        update_object(teacher)

        db.commit()

        return teacher


    @staticmethod
    def drop_teacher(db, user, teacher_id):
        require_admin(user)

        teacher = TeacherRepository.get_teacher_by_id(db, teacher_id)

        require_existence(teacher, MESSAGE_404_1)
        
        teacher.status = TeacherStatus.dropped
        teacher.user.is_active = False

        db.commit()


    @staticmethod
    def fire_teacher(db, user, teacher_id):
        require_admin(user)

        teacher = TeacherRepository.get_teacher_by_id(db, teacher_id)

        require_existence(teacher, MESSAGE_404_1)
        
        teacher.status = TeacherStatus.fired
        teacher.user.is_active = False

        db.commit()


    @staticmethod
    def assign_teacher_to_subject(db, user, teacher_subject_request):
        require_admin(user)

        assingment = TeacherSubject(**teacher_subject_request.model_dump())

        try:
            TeacherRepository.assign_teacher_to_subject(db, assingment)

            db.commit()
            db.refresh(assingment)

            return assingment
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail=MESSAGE_409)


    @staticmethod
    def withdraw_teacher_subject(db, user, assignment_id):
        require_admin(user)

        enrollment = TeacherRepository.get_teacher_subject_by_id(db, assignment_id)

        require_existence(enrollment, MESSAGE_404_2)

        enrollment.status = TeacherSubjectStatus.withdrawn

        db.commit()
    

    @staticmethod
    def update_teacher_subject(db, user, assignment_id, teacher_subject_update_info_request):
        require_admin(user)

        assignment = TeacherRepository.get_teacher_subject_by_id(db, assignment_id)

        require_existence(assignment, MESSAGE_404_2)

        update_object(assignment, teacher_subject_update_info_request)

        db.commit()

        return assignment
    

    @staticmethod
    def get_teachers_subjects(db, user):
        try:
            require_admin(user)

        finally:
            require_director(user)

        return TeacherRepository.get_teachers_subjects(db)
    

    @staticmethod
    def assign_head_of_class(db, user, teacher_group_request):
        require_admin(user)

        assignment = TeacherGroup(**teacher_group_request.model_dump())

        try:
            TeacherRepository.assign_head_of_class(db, assignment)

            db.commit()
            db.refresh(assignment)

            return assignment
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail=MESSAGE_409)


    @staticmethod
    def withdraw_teacher_group(db, user, assignment_id):
        require_admin(user)

        assignment = TeacherRepository.get_teacher_group_by_id(db, assignment_id)

        require_existence(assignment, MESSAGE_404_1)

        assignment.status = False

        db.commit()
    

    @staticmethod
    def update_teacher_group(db, user, assignment_id, teacher_group_update_info_request):
        require_admin(user)

        assignment = TeacherRepository.get_teacher_group_by_id(db, assignment_id)

        require_existence(assignment, MESSAGE_404_1)

        update_object(assignment, teacher_group_update_info_request)

        db.commit()

        return assignment
    

    @staticmethod
    def get_teachers_groups(db, user):
        try:
            require_admin(user)

        finally:
            require_director(user)

        return TeacherRepository.get_teachers_groups(db)