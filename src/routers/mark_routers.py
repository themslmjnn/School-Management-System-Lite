from fastapi import APIRouter, status, Depends, Path

from src.schemas.mark_schemas import MarkCreateGeneral, MarkResponseAdmin, MarkResponseGeneral, MarkUpdateInfoAdmin

from typing import Annotated
from sqlalchemy.orm import Session
from db.database import get_db
from src.services.group_services import GroupService
from core.security import get_current_user
from core.core_services import CoreService
from src.models.mark_model import Mark
router = APIRouter(
    tags=["Groups"]
)

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

path_param_ge1 = Annotated[int, Path(ge=1)]

@router.post("/teacher/putting_marks", response_model=MarkResponseGeneral, status_code=status.HTTP_201_CREATED)
def put_mark_teacher(db: db_dependency, user: user_dependency, mark_request: MarkCreateGeneral):
    return CoreService.add(db, user, mark_request, Mark)


@router.delete("/teacher/mark_deletion/{mark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mark_teacher(db: db_dependency, user: user_dependency, mark_id: path_param_ge1):
    CoreService.delete(db, user, mark_id)


@router.put("/teacher/mark_updating_indo/{mark_id}", response_model=MarkResponseGeneral, status_code=status.HTTP_200_OK)
def update_mark_info_admin(db: db_dependency, user: user_dependency, mark_id: path_param_ge1, mark_update_info_request: MarkUpdateInfoAdmin):
    return CoreService.update(db, user, mark_id, mark_update_info_request)


@router.get("/teacher/marks", response_model=list[MarkResponseGeneral], status_code=status.HTTP_200_OK)
def get_groups(db: db_dependency, user: user_dependency,):
    return CoreService.get_marks(db, user)
    