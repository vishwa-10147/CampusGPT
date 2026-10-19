# ==============================================================================
# CampusGPT Backend — Email Service
# ==============================================================================
import asyncio
import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode
from uuid import UUID

from app.core.config import settings
from app.core.security import create_email_verification_token

logger = logging.getLogger("campusgpt.email")


def _send_smtp(message: EmailMessage) -> None:
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


async def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email using the configured backend."""
    if settings.email_backend == "smtp":
        if not settings.smtp_host:
            raise RuntimeError("EMAIL_BACKEND=smtp requires SMTP_HOST")
        message = EmailMessage()
        message["From"] = settings.email_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        # smtplib is blocking; keep it off the event loop
        await asyncio.to_thread(_send_smtp, message)
    else:
        # Development: no mail server, so print the email where the developer can see it
        print(f"\n===== EMAIL to {to} =====\nSubject: {subject}\n\n{body}\n===== END EMAIL =====\n", flush=True)


def verification_link(user_id: UUID) -> str:
    token = create_email_verification_token(user_id)
    return f"{settings.frontend_url}/verify-email?{urlencode({'token': token})}"


async def send_verification_email(user_id: UUID, email: str) -> None:
    """Email the account's verification link. Failures are logged, not raised."""
    body = (
        "Welcome to CampusGPT!\n\n"
        "Confirm your email address to finish creating your account:\n\n"
        f"{verification_link(user_id)}\n\n"
        f"This link expires in {settings.email_verification_expire_hours} hours. "
        "If you didn't sign up, you can ignore this email."
    )
    try:
        await send_email(email, "Confirm your CampusGPT account", body)
    except Exception:
        logger.exception("Failed to send verification email to %s", email)
