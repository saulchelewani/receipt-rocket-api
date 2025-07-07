import os
from email.message import EmailMessage
from typing import List

import aiosmtplib
import jinja2

from core.settings import settings

template_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../templates"
)
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir), autoescape=jinja2.select_autoescape()
)


def render_template(template_name: str, context: dict) -> str:
    template = jinja_env.get_template(template_name)
    return template.render(context)


async def send_email(
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        attachments: List[dict] | None = None
) -> None:
    """
    Send an email using the configured SMTP server.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        attachments: List of attachment dictionaries with 'content' and 'filename' keys
        template_name:
        context:
    """
    html_body = render_template(template_name, context)
    plain_body = "This email requires an HTML-compatible email client."
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

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
