from email.message import EmailMessage
from typing import List

import aiosmtplib

from core.settings import settings


async def send_email(
        to_email: str,
        subject: str,
        message: str,
        attachments: List[dict] | None = None
) -> None:
    """
    Send an email using the configured SMTP server.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        message: Email body content
        attachments: List of attachment dictionaries with 'content' and 'filename' keys
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(message)

    if attachments:
        for attachment in attachments:
            msg.add_attachment(
                attachment["content"],
                filename=attachment["filename"]
            )

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        start_tls=settings.SMTP_USE_TLS,
    )
