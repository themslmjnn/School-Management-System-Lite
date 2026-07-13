from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_system_admin,
)
from src.users.schemas.guardian_link import (
    CreateGuardianLink,
    GuardianLinkResponse,
)
from src.users.services.system_admin import GuardianLinkServiceAdmin

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
    return await GuardianLinkServiceAdmin.link_guardian(
        db, current_user.id, link_request
    )
