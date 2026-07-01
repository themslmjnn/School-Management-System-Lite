from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import CurrentUser, async_db_dependency, require_guardian
from src.users.services.parent import UserServiceGuardian

router = APIRouter(
    prefix="/users",
    tags=["Users - Guardian"],
)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_own_account(
    db: async_db_dependency,
    current_user: Annotated[CurrentUser, Depends(require_guardian)],
):
    await UserServiceGuardian.delete_own_account(db, current_user.id)
