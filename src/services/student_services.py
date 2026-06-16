from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError

from src.models.student_model import Student, StudentStatus
from models.user import User
from src.models.association_models import StudentSubject
from src.models.association_models import StudentGroup
from src.repositories.student_repositories import StudentRepository
from src.repositories.user_repositories import UserRepository
from src.repositories.subject_repositories import SubjectRepository
from src.repositories.group_repositories import GroupRepository
from utils.helpers import require_admin, require_director, ensure_exists, hash_password, update_object


MESSAGE_404_1 = "Enrollment not found"
MESSAGE_404_2 = "Student not found"
MESSAGE_404_3 = "Subject not found"
MESSAGE_404_4 = "Group not found"
MESSAGE_409 = "Enrollment already exists"


class StudentService:
    @staticmethod
    def register_student(db, user, student_request, bcrypt_context):
        require_admin(user)

        try:
            user_data = student_request.user

            user = User(
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                date_of_birth=user_data.date_of_birth,
                address=user_data.address,
                email=user_data.email,
                phone_number=user_data.phone_number,
                password_hash=hash_password(user_data.password, bcrypt_context),
                role="student"
            )

            UserRepository.register_user(db, user)

            db.flush()

            student = Student(
                primary_info_id=user.id, 
                **student_request.student.model_dump(),
                status="enrolled"
            )

            StudentRepository.register_student(db, student)

            db.commit()
            db.refresh(student)

            return {"user": user, "student": student}
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Student already exists")
        

    @staticmethod
    def get_students(db, user):
        try:
            require_admin(user)
            
        except HTTPException:
            require_director(user)
        
        students = StudentRepository.get_students(db)

        return [
            {"user": student.user, "student": student}
            for student in students
        ]
    

    @staticmethod
    def update_student_info(db, user, student_id, student_update_info_request):
        require_admin(user)

        student = StudentRepository.get_student_by_id(db, student_id)

        ensure_exists(student, MESSAGE_404_2)
        
        update_object(student, student_update_info_request)

        if student.status in (StudentStatus.dropped, StudentStatus.graduated):
            student.user.is_active = False

        db.commit()

        return student


    @staticmethod
    def enroll_student_in_subject(db, user, enrollment_request):
        require_admin(user)

        enrollment = StudentSubject(**enrollment_request.model_dump())

        try:
            student = StudentRepository.get_student_by_id(db, enrollment.student_id)
            ensure_exists(student, MESSAGE_404_2)

            if student.status in (StudentStatus.dropped, StudentStatus.graduated):
                MESSAGE_400 = f"Student is {student.status.value}"

                raise HTTPException(status_code=400, detail=MESSAGE_400)

            subject = SubjectRepository.get_subject_by_id(db, enrollment.subject_id)
            ensure_exists(subject, MESSAGE_404_3)

            StudentRepository.enroll_student_in_subject(db, enrollment)

            db.commit()
            db.refresh(enrollment)

            return enrollment
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail=MESSAGE_409)
    

    @staticmethod
    def update_student_subject(db, user, enrollment_id, enrollment_update_info_request):
        require_admin(user)

        enrollment = StudentRepository.get_student_subject_by_id(db, enrollment_id)

        ensure_exists(enrollment, MESSAGE_404_1)

        if enrollment_update_info_request.student_id is not None:
            student = StudentRepository.get_student_by_id(db, enrollment_update_info_request.student_id)
            ensure_exists(student, MESSAGE_404_2)

            if student.status in (StudentStatus.dropped, StudentStatus.graduated):
                MESSAGE_400 = f"Student is {student.status.value}"

                raise HTTPException(status_code=400, detail=MESSAGE_400)
            
        if enrollment_update_info_request.subject_id is not None:
            try:
                subject = SubjectRepository.get_subject_by_id(db, enrollment_update_info_request.subject_id)
                ensure_exists(subject, MESSAGE_404_3)

            except IntegrityError:
                raise HTTPException(status_code=404, detail=MESSAGE_404_3)

        try:
            update_object(enrollment, enrollment_update_info_request)

            db.commit()

            return enrollment
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail=MESSAGE_409)
    

    @staticmethod
    def get_students_subjects(db, user):
        try:
            require_admin(user)

        except HTTPException:
            require_director(user)

        return StudentRepository.get_students_subjects(db)
    

    @staticmethod
    def add_student_to_group(db, user, enrollment_request):
        require_admin(user)

        enrollment = StudentGroup(**enrollment_request.model_dump())

        try:
            student = StudentRepository.get_student_by_id(db, enrollment.student_id)
            ensure_exists(student, MESSAGE_404_2)

            if student.status in (StudentStatus.dropped, StudentStatus.graduated):
                MESSAGE_400 = f"Student is {student.status.value}"

                raise HTTPException(status_code=400, detail=MESSAGE_400)

            subject = GroupRepository.get_group_by_id(db, enrollment.group_id)
            ensure_exists(subject, MESSAGE_404_4)

            StudentRepository.add_student_to_group(db, enrollment)

            db.commit()
            db.refresh(enrollment)

            return enrollment
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail=MESSAGE_409)
    

    @staticmethod
    def update_student_group(db, user, enrollment_id, student_group_update_info_request):
        require_admin(user)

        enrollment = StudentRepository.get_student_group_by_id(db, enrollment_id)

        ensure_exists(enrollment, MESSAGE_404_1)

        if student_group_update_info_request.student_id is not None:
            student = StudentRepository.get_student_by_id(db, student_group_update_info_request.student_id)
            ensure_exists(student, MESSAGE_404_2)

            if student.status in (StudentStatus.dropped, StudentStatus.graduated):
                MESSAGE_400 = f"Student is {student.status.value}"

                raise HTTPException(status_code=400, detail=MESSAGE_400)

        if student_group_update_info_request.group_id is not None:
            try:
                group = SubjectRepository.get_subject_by_id(db, student_group_update_info_request.group_id)
                ensure_exists(group, MESSAGE_404_4)

            except IntegrityError:
                raise HTTPException(status_code=404, detail=MESSAGE_404_4)

        try:
            update_object(enrollment, student_group_update_info_request)

            db.commit()

            return enrollment
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail=MESSAGE_409)


    @staticmethod
    def get_students_groups(db, user):
        try:
            require_admin(user)

        except HTTPException:
            require_director(user)

        return StudentRepository.get_students_groups(db)