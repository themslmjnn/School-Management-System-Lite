from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    require_roles,
)
from src.guardian_links.schemas import GuardianLinkResponse
from src.guardian_links.services.head_of_class import GuardianLinkServiceHeadOfClass
from src.utils.enums import UserRole

router = APIRouter(
    prefix="/guardian_links",
    tags=["Guardian Links - Head of Class"],
)


@router.get(
    "/my-students",
    response_model=list[GuardianLinkResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_student_links(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_roles(UserRole.TEACHER))],
):
    return await GuardianLinkServiceHeadOfClass.get_my_student_links(
        session, current_user.id
    )


@router.get(
    "/my-students/{link_id}",
    response_model=GuardianLinkResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_student_link_by_id(
    session: async_session_dependency,
    current_user: Annotated[CurrentUser, Depends(require_roles(UserRole.TEACHER))],
    link_id: Annotated[int, Path(ge=1)],
):
    return await GuardianLinkServiceHeadOfClass.get_my_student_link_by_id(
        session, current_user.id, link_id
    )
