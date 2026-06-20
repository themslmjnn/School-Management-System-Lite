from sqlalchemy.ext.asyncio import AsyncSession
from src.models.pending_emails import PendingEmail

class PendingEmailRepository:
    @staticmethod
    def add_pending_email(
        db: AsyncSession,
        *,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str,
        email_type: str,
        triggered_by: int | None = None,
        recipient_user_id: int | None = None,
    ) -> None:
        record = PendingEmail(
            recipient=recipient,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type=email_type,
            status="pending",
            triggered_by=triggered_by,
            recipient_user_id=recipient_user_id,
        )

        db.add(record)