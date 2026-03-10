from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError

from src.models.user_model import User
from src.models.teacher_model import Teacher, TeacherStatus


MESSAGE_404 = "Teacher not found"

class TeacherService:
    @staticmethod
    def register_teacher(db, user, teacher_request, bcrypt_context):

        CoreService.is_admin(user)

        try:
            user_data = teacher_request.teacher_primary_data

            teacher_primary_info = User(
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

            CoreRepository.add_item(db, teacher_primary_info)

            db.flush()

            teacher_advanced_info = Teacher(primary_info_id=teacher_primary_info.id, **teacher_request.teacher_advanced_data.model_dump())

            CoreRepository.add_item(db, teacher_advanced_info)

            db.commit()
            db.refresh(teacher_advanced_info)

            return {"teacher_primary_data": teacher_primary_info, "teacher_advanced_data": teacher_advanced_info}
        
        except IntegrityError:
            db.rollback()

            raise HTTPException(status_code=409, detail="Teacher already exists")
        

    @staticmethod
    def get_teachers_admin(db, user):
        CoreService.is_admin(user)

        teachers = CoreRepository.get_items(db, Teacher)

        return [
            {"teacher_primary_data": teacher.user, "teacher_advanced_data": teacher}
            for teacher in teachers
        ]
    

    @staticmethod
    def get_teachers_general(db, user):
        CoreService.does_have_access(user)

        teachers = CoreRepository.get_items(db, Teacher)

        return [
            {"teacher_primary_data": teacher.user, "teacher_advanced_data": teacher}
            for teacher in teachers
        ]
    

    @staticmethod
    def update_teacher_info_admin(db, user, teacher_id, teacher_update_info_request):
        CoreService.is_admin(user)

        teacher = CoreRepository.get_item_by_id(db, teacher_id, Teacher)


        if teacher is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        for field, value in teacher_update_info_request.model_dump(exclude_unset=True).items():
            setattr(teacher, field, value)

        db.commit()


    @staticmethod
    def drop_teacher_admin(db, user, teacher_id):
        CoreService.is_admin(user)
        teacher = CoreRepository.get_item_by_id(db, teacher_id, Teacher)


        if teacher is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        teacher.status = TeacherStatus.dropped
        teacher.user.is_active = False

        db.commit()


    @staticmethod
    def fire_teacher_admin(db, user, teacher_id):
        CoreService.is_admin(user)
        teacher = CoreRepository.get_item_by_id(db, teacher_id, Teacher)


        if teacher is None:
            raise HTTPException(status_code=404, detail=MESSAGE_404)
        
        teacher.status = TeacherStatus.fired
        teacher.user.is_active = False

        db.commit()