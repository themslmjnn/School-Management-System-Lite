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


def build_invite_email(invite_token: str, username: str) -> tuple[str, str, str]:
    activation_link = f"{settings.APP_URL}/auth/activation?token={invite_token}"

    subject = "Activate your LFGS account"

    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>

                <h2>You have been invited</h2>

                <p>An administrator created an account for you.</p>

                <p>
                    <strong>Username:</strong>
                    <span style="font-family:monospace;background:#f3f4f6;padding:2px 6px;border-radius:4px;">
                        {username}
                    </span>
                </p>

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
        f"You have been invited to LFGS | SMS Lite.\n\n"
        f"Username: {username}\n\n"
        f"Activate your account using the link below:\n\n"
        f"{activation_link}\n\n"
        f"This invitation expires in {settings.INVITE_TOKEN_EXPIRES_HOURS} hours.\n\n"
        f"If you were not expecting this email, ignore it."
    )

    return subject, html, text


async def send_invite_email(
    to_email: str, username: str, raw_invite_token: str
) -> None:
    subject, html, text = build_invite_email(raw_invite_token, username)

    await send(subject=subject, to_email=to_email, html_body=html, text_body=text)


async def send_account_info_updated_email(email: str) -> None:
    login_link = f"{settings.APP_URL}/auth/login"

    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;
                        padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>
                <h2>Your account information has been updated</h2>
                <p>
                    A school administrator has updated some information
                    associated with your account.
                </p>
                <div style="margin:40px 0;text-align:center;">
                    <a href="{login_link}"
                        style="background:#1d4ed8;color:white;padding:14px 28px;
                            border-radius:6px;text-decoration:none;font-weight:bold;">
                        Log In
                    </a>
                </div>
                <p>
                    If you did not request this change, please contact
                    your school administration as soon as possible.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        "LFGS | SMS Lite.\n\n"
        "A school administrator has updated some information associated "
        "with your account.\n\n"
        f"Log in at: {login_link}\n\n"
        "If you did not request this change, please contact "
        "your school administration as soon as possible."
    )

    await send(
        subject="Your account information has been updated",
        to_email=email,
        html_body=html,
        text_body=text,
    )


def build_admin_credentials_override_notification_email(
    old_username: str | None = None,
    new_username: str | None = None,
    old_email: str | None = None,
    new_email: str | None = None,
) -> tuple[str, str, str]:
    changes_html = ""
    changes_text = ""

    subject = "Your LFGS account credentials were changed"
    login_link = f"{settings.APP_URL}/auth/login"

    if old_username is not None and new_username is not None:
        changes_html += f"""
                    <tr>
                        <td style="padding:8px 0;color:#6b7280;font-size:13px;">
                            Old username
                        </td>
                        <td style="padding:8px 0;font-weight:bold;">{old_username}</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:#6b7280;font-size:13px;">
                            New username
                        </td>
                        <td style="padding:8px 0;font-weight:bold;">{new_username}</td>
                    </tr>
        """
        changes_text += (
            f"Old username: {old_username}\nNew username: {new_username}\n\n"
        )

    if old_email is not None and new_email is not None:
        changes_html += f"""
                    <tr>
                        <td style="padding:8px 0;color:#6b7280;font-size:13px;">
                            Old email
                        </td>
                        <td style="padding:8px 0;font-weight:bold;">{old_email}</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:#6b7280;font-size:13px;">
                            New email
                        </td>
                        <td style="padding:8px 0;font-weight:bold;">{new_email}</td>
                    </tr>
        """
        changes_text += f"Old email: {old_email}\nNew email: {new_email}\n\n"

    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;
                        padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>
                <h2>Your account credentials were changed</h2>
                <p>
                    An administrator has updated the credentials on your account.
                </p>
                <table style="width:100%;margin:24px 0;border-collapse:collapse;">
                    {changes_html}
                </table>
                <p>
                    If you were expecting this change, no action is needed.
                    You will need to log in again using your new credentials.
                </p>
                <div style="margin:40px 0;text-align:center;">
                    <a href="{login_link}"
                        style="background:#1d4ed8;color:white;padding:14px 28px;
                            border-radius:6px;text-decoration:none;font-weight:bold;">
                        Log In
                    </a>
                </div>
                <p>
                    If you were not expecting this change, contact your
                    administrator immediately.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        "LFGS | SMS Lite.\n\n"
        "An administrator has updated the credentials on your account.\n\n"
        f"{changes_text}"
        "If you were expecting this change, no action is needed. "
        "You will need to log in again using your new credentials.\n\n"
        f"Log in at: {login_link}\n\n"
        "If you were not expecting this change, contact your "
        "administrator immediately."
    )

    return subject, html, text


async def send_admin_credentials_override_notification(
    email: str,
    old_username: str | None = None,
    new_username: str | None = None,
    old_email: str | None = None,
    new_email: str | None = None,
) -> None:
    subject, html, text = build_admin_credentials_override_notification_email(
        old_username, new_username, old_email, new_email
    )

    await send(
        subject=subject,
        to_email=email,
        html_body=html,
        text_body=text,
    )


async def send_account_deactivation_email(email: str) -> None:
    html = """
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;
                        padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>

                <h2>Your account has been deactivated</h2>

                <p>
                    An administrator has deactivated your account.
                </p>

                <p>
                    If you believe this was done in error, please contact
                    your LFGS administrator.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        "LFGS | SMS Lite.\n\n"
        "An administrator has deactivated your account."
        "If you believe this was done in error, please contact "
        "your LFGS administrator."
    )

    await send(
        subject="Your LFGS account has been deactivated",
        to_email=email,
        html_body=html,
        text_body=text,
    )


async def send_account_activation_email(email: str) -> None:
    login_link = f"{settings.APP_URL}/auth/login"

    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;
                        padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>
                <h2>Your account has been activated</h2>
                <p>
                    An administrator has activated your account.
                    You can now log in and access the system.
                </p>
                <div style="margin:40px 0;text-align:center;">
                    <a href="{login_link}"
                        style="background:#1d4ed8;color:white;padding:14px 28px;
                            border-radius:6px;text-decoration:none;font-weight:bold;">
                        Log In
                    </a>
                </div>
                <p style="font-size:13px;color:#6b7280;">
                    If you were not expecting this, contact your administrator.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        "LFGS | SMS Lite.\n\n"
        "An administrator has activated your account. "
        "You can now log in and access the system.\n\n"
        f"Log in at: {login_link}\n\n"
        "If you were not expecting this, contact your administrator."
    )

    await send(
        subject="Your LFGS account has been activated",
        to_email=email,
        html_body=html,
        text_body=text,
    )


def build_reset_password_email(reset_password_token: str) -> tuple[str, str, str]:
    reset_link = f"{settings.APP_URL}/auth/reset_password?token={reset_password_token}"

    subject = "Your LFGS password reset link"

    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;
                        padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>
                <p>
                    An administrator has requested a password reset for your account.
                    Click the button below to set a new password.
                    This link expires in
                    <strong>{settings.RESET_PASSWORD_EXPIRES_MINUTES} minutes</strong>.
                </p>
                <div style="margin:40px 0;text-align:center;">
                    <a href="{reset_link}"
                        style="background:#1d4ed8;color:white;padding:14px 28px;
                            border-radius:6px;text-decoration:none;font-weight:bold;">
                        Reset Password
                    </a>
                </div>
                <p style="font-size:13px;color:#6b7280;">
                    If you were not expecting this, contact your administrator.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        f"LFGS | SMS Lite\n\n"
        f"An administrator has requested a password reset for your account.\n\n"
        f"Reset your password using the link below:\n\n"
        f"{reset_link}\n\n"
        f"This link expires in {settings.RESET_PASSWORD_EXPIRES_MINUTES} minutes.\n\n"
        f"If you were not expecting this, contact your administrator."
    )

    return subject, html, text


async def send_reset_password_token(email: str, raw_reset_token: str) -> None:
    subject, html, text = build_reset_password_email(raw_reset_token)

    await send(subject=subject, to_email=email, html_body=html, text_body=text)


async def send_email_change_verification(new_email: str, code: str) -> None:
    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;
                        padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>
                <h2>Confirm your new email address</h2>
                <p>
                    You requested to change your email address.
                    Enter the code below to confirm this new address.
                    It expires in
                    <strong>{settings.EMAIL_CHANGE_CODE_EXPIRES_MINUTES} minutes</strong>.
                </p>
                <div style="text-align:center;">
                    <div style="display:inline-block;background:#f0f4ff;
                                border:2px solid #1d4ed8;border-radius:8px;
                                padding:20px 48px;margin:24px 0;">
                        <span style="font-size:36px;font-weight:700;
                                    letter-spacing:10px;color:#1d4ed8;">
                            {code}
                        </span>
                    </div>
                </div>
                <p style="font-size:13px;color:#6b7280;">
                    If you did not request this change, ignore this email.
                    Your current email address has not been changed.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        f"LFGS | SMS Lite\n\n"
        f"You requested to change your email address.\n\n"
        f"Your confirmation code is: {code}\n\n"
        f"It expires in {settings.EMAIL_CHANGE_CODE_EXPIRES_MINUTES} minutes.\n\n"
        f"If you did not request this change, ignore this email. "
        f"Your current email address has not been changed."
    )

    await send(
        subject="Confirm your new LFGS email address",
        to_email=new_email,
        html_body=html,
        text_body=text,
    )


async def send_email_changed_notification(
    email: str, old_email: str, new_email: str
) -> None:
    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;
                        padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>
                <h2>Your email address was changed</h2>
                <p>
                    The email address associated with your account was
                    recently changed.
                </p>
                <table style="width:100%;margin:24px 0;border-collapse:collapse;">
                    <tr>
                        <td style="padding:8px 0;color:#6b7280;font-size:13px;">Old email</td>
                        <td style="padding:8px 0;font-weight:bold;">{old_email}</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;color:#6b7280;font-size:13px;">New email</td>
                        <td style="padding:8px 0;font-weight:bold;">{new_email}</td>
                    </tr>
                </table>
                <p>
                    If you made this change, no action is needed.
                </p>
                <p>
                    If you did not request this change, please contact
                    your school administration immediately.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        "LFGS | SMS Lite.\n\n"
        "The email address associated with your account was recently changed.\n\n"
        f"Old email: {old_email}\n"
        f"New email: {new_email}\n\n"
        "If you made this change, no action is needed.\n\n"
        "If you did not request this change, please contact "
        "your school administration immediately."
    )

    await send(
        subject="Your LFGS account email was changed",
        to_email=email,
        html_body=html,
        text_body=text,
    )


async def send_password_changed_notification(email: str) -> None:
    html = """
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;
                        padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>
                <h2>Your password was changed</h2>
                <p>
                    Your account password was successfully changed.
                    If you made this change, no action is needed.
                </p>
                <p>
                    If you did not change your password, contact your administrator
                    immediately as your account may be compromised.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        "LFGS | SMS Lite.\n\n"
        "Your account password was successfully changed.\n\n"
        "If you made this change, no action is needed.\n\n"
        "If you did not change your password, contact your administrator "
        "immediately as your account may be compromised."
    )

    await send(
        subject="Your LFGS password was changed",
        to_email=email,
        html_body=html,
        text_body=text,
    )


async def send_forgot_password_email(email: str, raw_reset_token: str) -> None:
    reset_link = f"{settings.APP_URL}/auth/reset-password?token={raw_reset_token}"

    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="font-family: Arial, sans-serif; background:#f4f4f5; padding:40px;">
            <div style="max-width:560px;margin:auto;background:white;
                        padding:40px;border-radius:8px;">
                <h1 style="color:#1d4ed8;">LFGS | SMS Lite</h1>
                <p>
                    You requested a password reset for your account.
                    Click the button below to set a new password.
                    This link expires in
                    <strong>{settings.RESET_PASSWORD_EXPIRES_MINUTES} minutes</strong>.
                </p>
                <div style="margin:40px 0;text-align:center;">
                    <a href="{reset_link}"
                        style="background:#1d4ed8;color:white;padding:14px 28px;
                            border-radius:6px;text-decoration:none;font-weight:bold;">
                        Reset Password
                    </a>
                </div>
                <p style="font-size:13px;color:#6b7280;">
                    If you did not request this, ignore this email.
                    Your password has not been changed.
                </p>
            </div>
        </body>
        </html>
    """

    text = (
        f"You requested a password reset for your "
        f"LFGS account.\n\n"
        f"Reset your password using the link below:\n\n"
        f"{reset_link}\n\n"
        f"This link expires in {settings.RESET_PASSWORD_EXPIRES_MINUTES} minutes.\n\n"
        f"If you did not request this, ignore this email. "
        f"Your password has not been changed."
    )

    await send(
        subject="Your LFGS password reset link",
        to_email=email,
        html_body=html,
        text_body=text,
    )
