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
    tags=["Marks"]
)

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

path_param_ge1 = Annotated[int, Path(ge=1)]

@router.post("/marks", response_model=MarkResponseGeneral, status_code=status.HTTP_201_CREATED)
def put_mark(db: db_dependency, user: user_dependency, mark_request: MarkCreateGeneral):
    return CoreService.add(db, user, mark_request, Mark)


@router.delete("/marks/{mark_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_mark(db: db_dependency, user: user_dependency, mark_id: path_param_ge1):
    CoreService.delete(db, user, mark_id)


@router.put("/mark/{mark_id}/update", response_model=MarkResponseGeneral, status_code=status.HTTP_200_OK)
def update_mark_info(db: db_dependency, user: user_dependency, mark_id: path_param_ge1, mark_update_info_request: MarkUpdateInfoAdmin):
    return CoreService.update(db, user, mark_id, mark_update_info_request)


@router.get("/marks", response_model=list[MarkResponseGeneral], status_code=status.HTTP_200_OK)
def get_groups(db: db_dependency, user: user_dependency,):
    return CoreService.get_marks(db, user)
    