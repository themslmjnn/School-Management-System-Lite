from fastapi import APIRouter, status, Depends, Path

from src.schemas.group_schemas import GroupResponseAdmin, GroupCreateAdmin, GroupUpdateInfoAdmin

from typing import Annotated
from sqlalchemy.orm import Session
from db.database import get_db
from src.services.group_services import GroupService
from core.security import get_current_user
router = APIRouter(
    tags=["Groups"]
)

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

path_param_ge1 = Annotated[int, Path(ge=1)]

@router.post("/admin/group_addition", response_model=GroupResponseAdmin, status_code=status.HTTP_201_CREATED)
def add_group_admin(db: db_dependency, user: user_dependency, group_request: GroupCreateAdmin):
    return GroupService.add_group_admin(db, user, group_request)


@router.delete("/admin/group_deletion/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_admin(db: db_dependency, user: user_dependency, group_id: path_param_ge1):
    GroupService.delete_group_admin(db, user, group_id)


@router.put("/admin/group_updating_indo/{group_id}", response_model=GroupResponseAdmin, status_code=status.HTTP_200_OK)
def update_group_info_admin(db: db_dependency, user: user_dependency, group_id: path_param_ge1, group_update_info_request: GroupUpdateInfoAdmin):
    return GroupService.update_group_info_admin(db, user, group_id, group_update_info_request)


@router.get("/admin/groups", response_model=list[GroupResponseAdmin], status_code=status.HTTP_200_OK)
def get_groups(db: db_dependency, user: user_dependency,):
    return GroupService.get_groups_admin(db, user)
    