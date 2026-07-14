from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import (
    CurrentUser,
    async_db_dependency,
    require_guardian,
)
from src.users.services.guardian import UserServiceGuardian

router = APIRouter(
    tags=["Users - Guardian"],
)


# COMPLETED!!!
@router.post("/users/me/deletion", status_code=status.HTTP_204_NO_CONTENT)
async def create_guardian_self_deletion_request(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_guardian)],
):
    await UserServiceGuardian.create_guardian_self_deletion_request(db, current_user.id)
