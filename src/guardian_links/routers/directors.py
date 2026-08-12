from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    pagination_dependency,
    require_directors,
)
from src.core.pagination import PaginatedResponse
from src.guardian_links.schemas import GuardianLinkResponse
from src.guardian_links.services.directors import GuardianLinkServiceDirector

router = APIRouter(
    prefix="/guardian_links",
    tags=["Guardian Links - Directors"],
)


@router.get(
    "/",
    response_model=PaginatedResponse[GuardianLinkResponse],
    status_code=status.HTTP_200_OK,
)
async def get_links(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_directors)],
    pagination: pagination_dependency,
):
    return await GuardianLinkServiceDirector.get_links(
        session, pagination.skip, pagination.limit
    )

@router.get(
    "/{link_id}",
    response_model=GuardianLinkResponse,
    status_code=status.HTTP_200_OK,
)
async def get_link_by_id_director(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_directors)],
    link_id: Annotated[int, Path(ge=1)],
):
    return await GuardianLinkServiceDirector.get_link_by_id(session, link_id)
