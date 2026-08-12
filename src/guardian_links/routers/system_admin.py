from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    require_system_admin,
)
from src.guardian_links.schemas import (
    CreateGuardianLinkAdmin,
    GuardianLinkResponseAdmin,
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
