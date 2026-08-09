from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    require_guardian,
)
from src.core.limiter import user_limiter
from src.users.services.guardian import UserServiceGuardian

router = APIRouter(
    tags=["Users - Guardian"],
)


@router.post("/users/me/deletion", status_code=status.HTTP_204_NO_CONTENT)
@user_limiter.limit("3/minute")
async def create_guardian_self_deletion_request(
    request: Request,
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_guardian)],
):
    await UserServiceGuardian.create_guardian_self_deletion_request(
        session, current_user.id
    )
