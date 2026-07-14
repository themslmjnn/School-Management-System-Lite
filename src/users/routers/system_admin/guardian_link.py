from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_system_admin,
)
from src.users.schemas.guardian_link import (
    CreateGuardianLinkAdmin,
    GuardianLinkResponseAdmin,
    UpdateGuardianPriorityAdmin,
)
from src.users.services.system_admin.guardian_link import GuardianLinkServiceAdmin

router = APIRouter(
    prefix="/users/guardians",
    tags=["Users - Guardian Links"],
)


@router.post(
    "", response_model=GuardianLinkResponseAdmin, status_code=status.HTTP_201_CREATED
)
async def link_guardian(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: CreateGuardianLinkAdmin,
):
    return await GuardianLinkServiceAdmin.link_guardian(
        db, current_user.id, create_request
    )


@router.delete("/{guardian_id}/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_guardian(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    guardian_id: int,
    student_id: int,
):
    await GuardianLinkServiceAdmin.unlink_guardian(
        db, current_user.id, guardian_id, student_id
    )


@router.patch(
    "/{guardian_id}/{student_id}",
    response_model=GuardianLinkResponseAdmin,
    status_code=status.HTTP_200_OK,
)
async def change_guardian_priority(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    guardian_id: int,
    student_id: int,
    update_request: UpdateGuardianPriorityAdmin,
):
    return await GuardianLinkServiceAdmin.change_priority(
        db, current_user.id, guardian_id, student_id, update_request
    )
