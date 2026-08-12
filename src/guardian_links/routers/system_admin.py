from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    require_system_admin,
)
from src.guardian_links.schemas import (
    CreateGuardianLinkAdmin,
    GuardianLinkResponseAdmin,
    UpdateGuardianPriorityAdmin,
)
from src.guardian_links.services.system_admin import GuardianLinkServiceAdmin

router = APIRouter(
    prefix="/guardian_links",
    tags=["Guardian Links - System Admin"],
)


@router.post(
    "",
    response_model=GuardianLinkResponseAdmin,
    status_code=status.HTTP_201_CREATED,
)
async def link_guardian(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    create_request: CreateGuardianLinkAdmin,
):
    return await GuardianLinkServiceAdmin.link_guardian(
        session, current_user.id, create_request
    )


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_guardian(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    link_id: Annotated[int, Path(ge=1)],
):
    await GuardianLinkServiceAdmin.unlink_guardian(session, current_user.id, link_id)


@router.patch("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def change_guardian_priority(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_system_admin)],
    link_id: Annotated[int, Path(ge=1)],
    update_request: UpdateGuardianPriorityAdmin,
):
    await GuardianLinkServiceAdmin.change_priority(
        session, current_user.id, link_id, update_request
    )
