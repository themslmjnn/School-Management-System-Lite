from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_roles,
    require_system_admin,
)
from src.users.schemas.guardian_link import (
    ChildResponse,
    CreateGuardianLink,
    GuardianLinkResponse,
    UpdateGuardianPriority,
)
from src.users.services.guardian_link import GuardianLinkService
from src.utils.enums import UserRole

router = APIRouter(
    prefix="/users/guardians",
    tags=["Users - Guardian Links"],
)


@router.post(
    "", response_model=GuardianLinkResponse, status_code=status.HTTP_201_CREATED
)
async def link_guardian(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    link_request: CreateGuardianLink,
):
    return await GuardianLinkService.link(db, current_user.id, link_request)


@router.delete("/{guardian_id}/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_guardian(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    guardian_id: int,
    student_id: int,
):
    await GuardianLinkService.unlink(db, current_user.id, guardian_id, student_id)


@router.patch(
    "/{guardian_id}/{student_id}",
    response_model=GuardianLinkResponse,
    status_code=status.HTTP_200_OK,
)
async def change_guardian_priority(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    guardian_id: int,
    student_id: int,
    update_request: UpdateGuardianPriority,
):
    return await GuardianLinkService.change_priority(
        db, current_user.id, guardian_id, student_id, update_request
    )


@router.get("/me/children", response_model=list[ChildResponse])
async def get_my_children(
    db: async_db_dependency,
    current_user: Annotated[
        CurrentUser, Depends(require_roles(*(UserRole.__members__.values())))
    ],
):
    return await GuardianLinkService.get_children_for_guardian(db, current_user.id)
