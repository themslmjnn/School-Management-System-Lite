from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from guardian_links.services.student import GuardianLinkServiceSelf
from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    require_roles,
)
from src.guardian_links.schemas import GuardianLinkResponse
from src.utils.enums import UserRole

router = APIRouter(
    prefix="/guardian_links",
    tags=["Guardian Links - Head of Class"],
)


@router.get(
    "/my-guardians",
    response_model=list[GuardianLinkResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_links_as_student(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_roles(UserRole.STUDENT))],
):
    return await GuardianLinkServiceSelf.get_my_links_as_student(
        session, current_user.id
    )


@router.get(
    "/my-guardians/{link_id}",
    response_model=GuardianLinkResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_link_as_student_by_id(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_roles(UserRole.STUDENT))],
    link_id: Annotated[int, Path(ge=1)],
):
    return await GuardianLinkServiceSelf.get_my_link_as_student_by_id(
        session, current_user.id, link_id
    )
