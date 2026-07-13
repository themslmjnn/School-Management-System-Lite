from fastapi import APIRouter, status

from src.core.dependencies import async_db_dependency, current_user_dependency
from src.users.services.guardian import UserServiceGuardian

router = APIRouter(
    tags=["Users - Guardian"],
)


@router.post("/users/me/deletion", status_code=status.HTTP_204_NO_CONTENT)
async def create_guardian_self_deletion_request(
    db: async_db_dependency,
    current_user: current_user_dependency,
):
    return await UserServiceGuardian.create_guardian_self_deletion_request(
        db, current_user.id
    )
