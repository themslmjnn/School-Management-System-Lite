from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import (
    CurrentUser,
    async_session_dependency,
    pagination_dependency,
    require_system_admin,
)
from src.core.pagination import PaginatedResponse
from src.emails.schemas import PendingEmailResponse
from src.emails.service import PendingEmailService

router = APIRouter(
    prefix="/emails",
    tags=["Emails - System Admin"],
)


@router.get(
    "/failed",
    response_model=PaginatedResponse[PendingEmailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_failed_emails(
    session: async_session_dependency,
    pagination: pagination_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
):
    return await PendingEmailService.get_failed_emails(
        session,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.post("/{email_id}/retry", status_code=status.HTTP_204_NO_CONTENT)
async def retry_failed_email(
    session: async_session_dependency,
    _: Annotated[CurrentUser, Depends(require_system_admin)],
    email_id: Annotated[int, Path(ge=1)],
):
    await PendingEmailService.retry_failed_email(session, email_id)
