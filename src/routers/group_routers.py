from fastapi import APIRouter, status, Depends, Path

from src.schemas.group_schemas import GroupResponseAdmin, GroupCreateAdmin, GroupUpdateInfoAdmin

from typing import Annotated
from db.database import db_dependency
from src.services.group_services import GroupService
from core.security import user_dependency


router = APIRouter(tags=["Groups"])

@router.post("/groups", response_model=GroupResponseAdmin, status_code=status.HTTP_201_CREATED)
def add_group(db: db_dependency, user: user_dependency, group_request: GroupCreateAdmin):
    return GroupService.add_group(db, user, group_request)


@router.delete("/groups/{group_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(db: db_dependency, user: user_dependency, group_id: int):
    GroupService.delete_group(db, user, group_id)


@router.put("/groups/{group_id}/update", response_model=GroupResponseAdmin, status_code=status.HTTP_200_OK)
def update_group_info(db: db_dependency, user: user_dependency, group_id: int, group_update_info_request: GroupUpdateInfoAdmin):
    return GroupService.update_group_info(db, user, group_id, group_update_info_request)


@router.get("/groups", response_model=list[GroupResponseAdmin], status_code=status.HTTP_200_OK)
def get_groups(db: db_dependency, user: user_dependency,):
    return GroupService.get_groups(db, user)
    