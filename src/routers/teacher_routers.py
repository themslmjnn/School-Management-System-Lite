from fastapi import APIRouter

from starlette import status

from core.security import user_dependency, bcrypt_context
from database import db_dependency
from src.schemas.teacher_schemas import (
    TeacherCreateAdmin,
    TeacherResponseAdmin,
    TeacherUpdateInfoAdmin,
)
from src.schemas.teacher_schemas import (
    TeacherSubjectResponseAdmin,
    TeacherSubjectCreateAdmin,
    TeacherSubjectUpdateInfoAdmin,
)
from src.schemas.teacher_schemas import (
    TeacherGroupCreateAdmin,
    TeacherGroupResponseAdmin,
    TeacherGroupUpdateInfoAdmin,
)
from src.services.teacher_services import TeacherService


router = APIRouter(tags=["Teachers"])


@router.post(
    "/teachers",
    response_model=TeacherResponseAdmin,
    status_code=status.HTTP_201_CREATED,
)
def register_teacher(
    db: db_dependency, user: user_dependency, teacher_request: TeacherCreateAdmin
):

    return TeacherService.register_teacher(db, user, teacher_request, bcrypt_context)


@router.get(
    "/teachers",
    response_model=list[TeacherResponseAdmin],
    status_code=status.HTTP_200_OK,
)
def get_teachers(db: db_dependency, user: user_dependency):

    return TeacherService.get_teachers(db, user)


@router.put("/teachers/{teacher_id}/update", status_code=status.HTTP_204_NO_CONTENT)
def update_teacher_info(
    db: db_dependency,
    user: user_dependency,
    teacher_id: int,
    teacher_update_info_request: TeacherUpdateInfoAdmin,
):

    return TeacherService.update_teacher_info(
        db, user, teacher_id, teacher_update_info_request
    )


# @router.put("/teachers/{teacher_id}/drop", status_code=status.HTTP_204_NO_CONTENT)
# def drop_teacher(
#     db: db_dependency, user: user_dependency, teacher_id: int):

#     TeacherService.drop_teacher(db, user, teacher_id)


# @router.put("/teachers/{teacher_id}/fire", status_code=status.HTTP_204_NO_CONTENT)
# def fire_teacher(db: db_dependency, user: user_dependency, teacher_id: int):

#     TeacherService.fire_teacher(db, user, teacher_id)


@router.post(
    "/teachers/subjects",
    response_model=TeacherSubjectResponseAdmin,
    status_code=status.HTTP_201_CREATED,
)
def assign_teacher_to_subject(
    db: db_dependency,
    user: user_dependency,
    teacher_subject_request: TeacherSubjectCreateAdmin,
):

    return TeacherService.assign_teacher_to_subject(db, user, teacher_subject_request)


# @router.put("/teachers/subjects/{assignment_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
# def withdraw_teacher_subject(
#         db: db_dependency,
#         user: user_dependency,
#         assignment_id: int):

#     TeacherService.withdraw_teacher_subject(db, user, assignment_id)


@router.put(
    "/teachers/subjects/{assignment_id}/update",
    response_model=TeacherSubjectResponseAdmin,
    status_code=status.HTTP_200_OK,
)
def update_teacher_subject(
    db: db_dependency,
    user: user_dependency,
    assignment_id: int,
    teacher_subject_update_info_request: TeacherSubjectUpdateInfoAdmin,
):

    return TeacherService.update_teacher_subject(
        db, user, assignment_id, teacher_subject_update_info_request
    )


@router.get(
    "/teachers/subjects",
    response_model=list[TeacherSubjectResponseAdmin],
    status_code=status.HTTP_200_OK,
)
def get_teachers_subjects(db: db_dependency, user: user_dependency):

    return TeacherService.get_teachers_subjects(db, user)


@router.post(
    "/teachers/groups",
    response_model=TeacherGroupResponseAdmin,
    status_code=status.HTTP_201_CREATED,
)
def assign_head_of_class(
    db: db_dependency,
    user: user_dependency,
    teacher_group_request: TeacherGroupCreateAdmin,
):

    return TeacherService.assign_head_of_class(db, user, teacher_group_request)


# @router.put("/teachers/groups/{assignment_id}/withdraw", status_code=status.HTTP_204_NO_CONTENT)
# def withdraw_teacher_group(
#         db: db_dependency,
#         user: user_dependency,
#         assignment_id: int):

#     TeacherService.withdraw_teacher_group(db, user, assignment_id)


@router.put(
    "/teachers/groups/{assignment_id}/update",
    response_model=TeacherGroupResponseAdmin,
    status_code=status.HTTP_200_OK,
)
def update_teacher_group(
    db: db_dependency,
    user: user_dependency,
    assignment_id: int,
    teacher_group_update_info_request: TeacherGroupUpdateInfoAdmin,
):

    return TeacherService.update_teacher_group(
        db, user, assignment_id, teacher_group_update_info_request
    )


@router.get(
    "/teaches/groups",
    response_model=list[TeacherGroupResponseAdmin],
    status_code=status.HTTP_200_OK,
)
def get_teachers_groups(db: db_dependency, user: user_dependency):

    return TeacherService.get_teachers_groups(db, user)
