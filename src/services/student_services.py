from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError

from src.models.student_model import Student, StudentStatus
from src.models.user_model import User
from src.repositories.student_repositories import StudentRepository


MESSAGE_404 = "Student not found"
MESSAGE_409 = "Duplicate values are not accepted"


class StudentService:
    # Done
    @staticmethod
    def register_student(db, student_request, bcrypt_context):
        try:
            user_data = student_request.user_data

            student_primary_info = User(
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                date_of_birth=user_data.date_of_birth,
                address=user_data.address,
                email=user_data.email,
                phone_number=user_data.phone_number,
                password_hash=bcrypt_context.hash(user_data.password),
                role="students"
            )

            StudentRepository.add(db, student_primary_info)

            db.flush()

            student_advanced_info = Student(primary_info_id=student_primary_info.id, **student_request.student_advanced_data.model_dump())

            StudentRepository.add(db, student_advanced_info)

            db.commit()
            db.refresh(student_advanced_info)

            return {"user_data": student_primary_info, "student_advanced_data": student_advanced_info}
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Student already exists")
        

    # Done
    @staticmethod
    def get_all_users(db):
        students = StudentRepository.get_users(db)

        return [
            {"user_data": student.user, "student_advanced_data": student}
            for student in students
        ]


    @staticmethod
    def update_student_info(db, student_id, student_update_info_request):
        student = StudentRepository.get_student_by_id(db, student_id)

        if student is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        for field, value in student_update_info_request.model_dump(exclude_unset=True).items():
            setattr(student, field, value)

        db.commit()

        return student


    @staticmethod
    def graduate_student(db, student_id):
        student = StudentRepository.get_student_by_id(db, student_id)

        if student is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        student.status = StudentStatus.graduated
        student.user.is_active = False

        db.commit()



    @staticmethod
    def drop_student(db, student_id):
        student = StudentRepository.get_student_by_id(db, student_id)

        if student is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        student.status = StudentStatus.dropped
        student.user.is_active = False

        db.commit()

        


    