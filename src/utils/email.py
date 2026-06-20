import urllib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import httpx

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


async def _send_via_resend(
    subject: str,
    to_email: str,
    html_body: str,
    text_body: str,
) -> None:
    payload = {
        "from": f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>",
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            json=payload,
            headers=headers,
            timeout=10.0,
        )

    response.raise_for_status()

    logger.info(
        "email_sent",
        to_email=to_email,
        subject=subject,
    )


async def _send_via_mailtrap(
    subject: str,
    to_email: str,
    html_body: str,
    text_body: str,
) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    message["To"] = to_email

    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(
        message,
        hostname=settings.MAILTRAP_HOST,
        port=settings.MAILTRAP_PORT,
        username=settings.MAILTRAP_USERNAME,
        password=settings.MAILTRAP_PASSWORD,
        start_tls=True,
    )

    logger.info(
        "email_sent_mailtrap",
        to_email=to_email,
        subject=subject,
    )


async def send(
    subject: str,
    to_email: str,
    html_body: str,
    text_body: str,
) -> None:
    if settings.ENVIRONMENT == "development":
        await _send_via_mailtrap(subject, to_email, html_body, text_body)
    else:
        await _send_via_resend(subject, to_email, html_body, text_body)


async def send_safe(coro, **log_context) -> None:
    try:
        await coro
    except Exception as exc:
        logger.error(
            "background_email_task_failed",
            error=str(exc),
            error_type=type(exc).__name__,
            **log_context,
        )


def build_invite_email(invite_token: str, email: str) -> tuple[str, str, str]:
    encoded_email = urllib.parse.quote(email)
    activation_link = (
        f"{settings.APP_URL}/auth/activate_with_token"
        f"?token={invite_token}"
        f"&email={encoded_email}"
    )

    subject = "Activate your Library account"

    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">Library Management System</h1>
                <h2>You have been invited</h2>
                <p>An administrator created an account for you.</p>
                <p>
                    Click the button below to activate your account and set your password.
                    This invitation expires in
                    <strong>{settings.INVITE_TOKEN_EXPIRES_HOURS} hours</strong>.
                </p>
                <div style="margin:40px 0;text-align:center;">
                    <a href="{activation_link}"
                        style="background:#1d4ed8;color:white;padding:14px 28px;
                            border-radius:6px;text-decoration:none;font-weight:bold;">
                        Activate Account
                    </a>
                </div>
                <p style="font-size:13px;color:#6b7280;">
                    If you were not expecting this email, ignore it.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        f"You have been invited to the Library Management System.\n\n"
        f"Activate your account using the link below:\n\n"
        f"{activation_link}\n\n"
        f"This invitation expires in {settings.INVITE_TOKEN_EXPIRES_HOURS} hours.\n\n"
        f"If you were not expecting this email, ignore it."
    )

    return subject, html, text


async def send_invite_email(email: str, raw_invite_token: str) -> None:
    subject, html, text = build_invite_email(raw_invite_token, email)

    await send(subject=subject, to_email=email, html_body=html, text_body=text)
