from fastapi import APIRouter, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import current_user_dependency
from users.services.guardian import UserServiceGuardian

router = APIRouter(
    tags=["Users - Guardian"],
)


@router.post("/users/me/deletion", status_code=status.HTTP_204_NO_CONTENT)
async def create_guardian_self_deletion_request(
    db: AsyncSession,
    current_user: current_user_dependency,
):
    return UserServiceGuardian.create_guardian_self_deletion_request(
        db, current_user.id
    )
