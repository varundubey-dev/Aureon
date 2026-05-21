import smtplib
from fastapi import status
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.core.exceptions.auth import AuthError


def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> bool:
    try:
        message = MIMEMultipart()

        message["From"] = settings.EMAIL_FROM
        message["To"] = recipient
        message["Subject"] = subject

        message.attach(MIMEText(body, "html"))

        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
        ) as server:

            server.starttls()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

            server.send_message(message)

        return True

    except smtplib.SMTPException:

        raise AuthError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Email service temporarily unavailable",
        )

    except Exception:

        raise AuthError(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to send email",
        )
