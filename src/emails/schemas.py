from datetime import datetime

from pydantic import BaseModel, field_serializer

from src.utils.base_schema import BaseSchema
from src.utils.enums import EmailSendingStatus, EmailType


class PendingEmailResponse(BaseModel):
    recipient: str
    subject: str

    email_type: str
    status: str

    triggered_by: int | None
    recipient_user_id: int | None


class PendingEmailResponseCache(PendingEmailResponse, BaseSchema):
    id: int

    retry_count: int
    last_error: str | None

    sent_at: datetime | None

    created_at: datetime


class PendingEmailResponseDetailed(PendingEmailResponseCache):
    @field_serializer("created_at", "sent_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None

        return value.strftime("%d %b %Y, %H:%M")


class SearchEmailAdmin(BaseModel):
    status: EmailSendingStatus | None = None
    email_type: EmailType | None = None
    recipient_user_id: int | None = None
    triggered_by: int | None = None
