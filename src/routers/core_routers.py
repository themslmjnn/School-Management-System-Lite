from fastapi import APIRouter, status, Depends, Path

from src.schemas.core_schemas import StudentGroupCreateAdmin, StudentGroupResponseAdmin, StudentSubjectCreateAdmin, StudentSubjectResponseAdmin, TeacherGroupCreateAdmin, TeacherGroupResponseAdmin, TeacherGroupUpdateInfoAdmin, TeacherSubjectCreateAdmin, TeacherSubjectResponseAdmin, StudentSubjectUpdateInfoAdmin, StudentGroupUpdateInfoAdmin, TeacherSubjectUpdateInfoAdmin

from typing import Annotated
from sqlalchemy.orm import Session
from db.database import get_db
from core.core_services import CoreService
from core.security import get_current_user
router = APIRouter(
    tags=["Groups"]
)

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

path_param_ge1 = Annotated[int, Path(ge=1)]

@router.post("/admin/student_subject_addition", response_model=StudentSubjectResponseAdmin, status_code=status.HTTP_201_CREATED)
def add_student_subject_admin(db: db_dependency, user: user_dependency, student_subject_request: StudentSubjectCreateAdmin):
    return CoreService.add(db, user, student_subject_request)


@router.delete("/admin/student_subject_deletion/{student_subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_subject_admin(db: db_dependency, user: user_dependency, student_subject_id: path_param_ge1):
    CoreService.delete(db, user, student_subject_id)


@router.put("/admin/student_subject_updating_indo/{student_subject_id}", response_model=StudentSubjectResponseAdmin, status_code=status.HTTP_200_OK)
def update_student_subject_info_admin(db: db_dependency, user: user_dependency, student_subject_id: path_param_ge1, student_subject_update_info_request: StudentSubjectUpdateInfoAdmin):
    return CoreService.update(db, user, student_subject_id, student_subject_update_info_request)


@router.get("/admin/student_subjects", response_model=list[StudentSubjectResponseAdmin], status_code=status.HTTP_200_OK)
def get_student_subjects(db: db_dependency, user: user_dependency,):
    return CoreService.get_student_subjects(db, user)
    



@router.post("/admin/student_group_addition", response_model=StudentGroupResponseAdmin, status_code=status.HTTP_201_CREATED)
def add_student_group_admin(db: db_dependency, user: user_dependency, student_group_request: StudentGroupCreateAdmin):
    return CoreService.add(db, user, student_group_request)


@router.delete("/admin/student_group_deletion/{student_group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_group_admin(db: db_dependency, user: user_dependency, student_group_id: path_param_ge1):
    CoreService.delete(db, user, student_group_id)


@router.put("/admin/student_group_updating_indo/{student_group_id}", response_model=StudentGroupResponseAdmin, status_code=status.HTTP_200_OK)
def update_student_group_info_admin(db: db_dependency, user: user_dependency, student_group_id: path_param_ge1, student_group_update_info_request: StudentGroupUpdateInfoAdmin):
    return CoreService.update(db, user, student_group_id, student_group_update_info_request)


@router.get("/admin/student_groups", response_model=list[StudentGroupResponseAdmin], status_code=status.HTTP_200_OK)
def get_student_groups(db: db_dependency, user: user_dependency,):
    return CoreService.get_student_groups(db, user)






@router.post("/admin/teacher_subject_addition", response_model=TeacherSubjectResponseAdmin, status_code=status.HTTP_201_CREATED)
def add_teacher_subject_admin(db: db_dependency, user: user_dependency, teacher_subject_request: TeacherSubjectCreateAdmin):
    return CoreService.add(db, user, teacher_subject_request)


@router.delete("/admin/teacher_subject_deletion/{teacher_subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher_subject_admin(db: db_dependency, user: user_dependency, teacher_subject_id: path_param_ge1):
    CoreService.delete(db, user, teacher_subject_id)


@router.put("/admin/teacher_subject_updating_indo/{teacher_subject_id}", response_model=TeacherSubjectResponseAdmin, status_code=status.HTTP_200_OK)
def update_teacher_subject_info_admin(db: db_dependency, user: user_dependency, teacher_subject_id: path_param_ge1, teacher_subject_update_info_request: TeacherSubjectUpdateInfoAdmin):
    return CoreService.update(db, user, teacher_subject_id, teacher_subject_update_info_request)


@router.get("/admin/teacher_subjects", response_model=list[TeacherSubjectResponseAdmin], status_code=status.HTTP_200_OK)
def get_teacher_subjects(db: db_dependency, user: user_dependency,):
    return CoreService.get_teacher_subjects(db, user)





@router.post("/admin/teacher_group_addition", response_model=TeacherGroupResponseAdmin, status_code=status.HTTP_201_CREATED)
def add_teacher_group_admin(db: db_dependency, user: user_dependency, teacher_group_request: TeacherGroupCreateAdmin):
    return CoreService.add(db, user, teacher_group_request)


@router.delete("/admin/teacher_group_deletion/{teacher_group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher_group_admin(db: db_dependency, user: user_dependency, teacher_group_id: path_param_ge1):
    CoreService.delete(db, user, teacher_group_id)


@router.put("/admin/teacher_group_updating_indo/{teacher_group_id}", response_model=TeacherGroupResponseAdmin, status_code=status.HTTP_200_OK)
def update_teacher_group_info_admin(db: db_dependency, user: user_dependency, teacher_group_id: path_param_ge1, teacher_group_update_info_request: TeacherGroupUpdateInfoAdmin):
    return CoreService.update(db, user, teacher_group_id, teacher_group_update_info_request)


@router.get("/admin/teacher_groups", response_model=list[TeacherGroupResponseAdmin], status_code=status.HTTP_200_OK)
def get_teacher_groups(db: db_dependency, user: user_dependency,):
    return CoreService.get_teacher_groups(db, user)