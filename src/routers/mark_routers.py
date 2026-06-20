from fastapi import APIRouter

from starlette import status

from database import db_dependency
from core.security import user_dependency
from src.schemas.mark_schemas import (
    MarkCreateTeacher,
    MarkResponsePublic,
    MarkUpdateInfoAdmin,
)
from src.services.mark_services import MarkService


router = APIRouter(tags=["Marks"])


@router.post(
    "/marks", response_model=MarkResponsePublic, status_code=status.HTTP_201_CREATED
)
def put_mark(db: db_dependency, user: user_dependency, mark_request: MarkCreateTeacher):

    return MarkService.put_mark(db, user, mark_request)


@router.delete("/marks/{mark_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_mark(db: db_dependency, user: user_dependency, mark_id: int):

    MarkService.delete_mark(db, user, mark_id)


@router.put(
    "/mark/{mark_id}/update",
    response_model=MarkResponsePublic,
    status_code=status.HTTP_200_OK,
)
def update_mark_info(
    db: db_dependency,
    user: user_dependency,
    mark_id: int,
    mark_update_info_request: MarkUpdateInfoAdmin,
):

    return MarkService.update_mark_info(db, user, mark_id, mark_update_info_request)


@router.get(
    "/marks", response_model=list[MarkResponsePublic], status_code=status.HTTP_200_OK
)
def get_groups(db: db_dependency, user: user_dependency):

    return MarkService.get_marks(db, user)
