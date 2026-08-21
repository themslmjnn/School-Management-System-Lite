from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    pagination_dependency,
    require_system_admin,
)
from src.core.pagination import PaginatedResponse
from src.emails.schemas import PendingEmailResponseDetailed, SearchEmailAdmin
from src.emails.service import PendingEmailService
from src.utils.enums import EmailSortField, OrderBy

router = APIRouter(
    prefix="/emails",
    tags=["Emails - System Admin"],
)


@router.get(
    "",
    response_model=PaginatedResponse[PendingEmailResponseDetailed],
    status_code=status.HTTP_200_OK,
)
async def get_emails(
    session: async_session_dependency,
    pagination: pagination_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    filters: Annotated[SearchEmailAdmin, Depends()],
    sort_by: Annotated[EmailSortField, Query()] = EmailSortField.CREATED_AT,
    order: Annotated[OrderBy, Query()] = OrderBy.DESC,
):
    return await PendingEmailService.get_emails(
        session,
        skip=pagination.skip,
        limit=pagination.limit,
        filters=filters,
        sort_by=sort_by,
        order=order,
    )


@router.get(
    "/{email_id}",
    response_model=PendingEmailResponseDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_email_by_id(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    email_id: Annotated[int, Path(ge=1)],
):
    return await PendingEmailService.get_email_by_id(session, email_id)
