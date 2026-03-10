from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError

from src.models.student_model import Student, StudentStatus
from src.models.user_model import User
from src.models.association_models import StudentSubject, StudentSubjectStatus
from src.models.association_models import StudentGroup, StudentGroupStatus
from src.repositories.student_repositories import StudentRepository
from src.repositories.user_repositories import UserRepository
from utils.helpers import require_admin, require_director, require_existence, hash_password, update_object


MESSAGE_404 = "Enrollment not found"
MESSAGE_409 = "Enrollment already exists"


class StudentService:
    @staticmethod
    def register_student(db, user, student_request, bcrypt_context):
        require_admin(user)

        try:
            user_data = student_request.user_data

            user = User(
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                date_of_birth=user_data.date_of_birth,
                address=user_data.address,
                email=user_data.email,
                phone_number=user_data.phone_number,
                password_hash=hash_password(user_data.password, bcrypt_context)
            )

            UserRepository.register_user(db, user)

            db.flush()

            student = Student(primary_info_id=user.id, **student_request.student.model_dump())

            StudentRepository.register_student(db, student)

            db.commit()
            db.refresh(student)

            return {"user": user, "student": student}
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Student already exists")
        

    @staticmethod
    def get_students(db, user):
        if require_admin(user) is None:
            students = StudentRepository.get_students_admin(db)
        elif require_director(user) is None:
            students = StudentRepository.get_students_public(db)

        return [
            {"user": student.user, "student": student}
            for student in students
        ]
    

    @staticmethod
    def update_student_info(db, user, student_id, student_update_info_request):
        require_admin(user)

        student = StudentRepository.get_student_by_id(db, student_id)

        require_existence(student)
        
        update_object(student, student_update_info_request)

        db.commit()

        return student


    @staticmethod
    def graduate_student(db, user, student_id):
        require_admin(user)

        student = StudentRepository.get_student_by_id(db, student_id)

        require_existence(student)
        
        student.status = StudentStatus.graduated
        student.user.is_active = False

        db.commit()


    @staticmethod
    def drop_student(db, user, student_id):
        require_admin(user)

        student = StudentRepository.get_student_by_id(db, student_id)

        require_existence(student)
        
        student.status = StudentStatus.dropped
        student.user.is_active = False

        db.commit()


    @staticmethod
    def enroll_student_in_subject(db, user, enrollment_request):
        require_admin(user)

        enrollment = StudentSubject(**enrollment_request.model_dump())

        try:
            StudentRepository.enroll_student_in_subject(db, enrollment)

            db.commit()
            db.refresh(enrollment)

            return enrollment
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail=MESSAGE_409)


    @staticmethod
    def withdraw_student_subject_enrollment(db, user, enrollment_id):
        require_admin(user)

        enrollment = StudentRepository.get_student_subject_by_id(db, enrollment_id)

        require_existence(enrollment, MESSAGE_404)

        enrollment.status = StudentSubjectStatus.withdrawn

        db.commit()
    

    @staticmethod
    def update_student_subject(db, user, enrollment_id, enrollment_update_info_request):
        require_admin(user)

        enrollment = StudentRepository.get_student_subject_by_id(db, enrollment_id)

        require_existence(enrollment, MESSAGE_404)

        update_object(enrollment, enrollment_update_info_request)

        db.commit()

        return enrollment
    

    @staticmethod
    def get_students_subjects(db, user):
        try:
            require_admin(user)

        finally:
            require_director(user)

        return StudentRepository.get_students_subjects(db)
    

    @staticmethod
    def add_student_to_group(db, user, enrollment_request):
        require_admin(user)

        enrollment = StudentGroup(**enrollment_request.model_dump())

        try:
            StudentRepository.add_student_to_group(db, enrollment)

            db.commit()
            db.refresh(enrollment)

            return enrollment
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail=MESSAGE_409)


    @staticmethod
    def remove_student_from_group(db, user, enrollment_id):
        require_admin(user)

        enrollment = StudentRepository.get_student_group_by_id(db, enrollment_id)

        require_existence(enrollment, MESSAGE_404)

        enrollment.status = StudentGroupStatus.dropped

        db.commit()
    

    @staticmethod
    def update_student_group(db, user, enrollment_id, student_group_update_info_request):
        require_admin(user)

        enrollment = StudentRepository.get_student_subject_by_id(db, enrollment_id)

        require_existence(enrollment, MESSAGE_404)

        update_object(enrollment, student_group_update_info_request)

        db.commit()

        return enrollment
    

    @staticmethod
    def get_students_groups(db, user):
        try:
            require_admin(user)

        finally:
            require_director(user)

        return StudentRepository.get_students_groups(db)