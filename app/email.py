"""Email notification utility."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger(__name__)


def send_email(subject: str, body: str) -> bool:
    """Send a notification email. Returns True on success, False on failure."""
    if not all([settings.email_sender, settings.email_password, settings.email_recipient]):
        logger.warning(
            "Email not configured — skipped. Subject: %s | Body: %s", subject, body
        )
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.email_sender
        msg["To"] = settings.email_recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.email_sender, settings.email_password)
            server.sendmail(settings.email_sender, settings.email_recipient, msg.as_string())

        logger.info("Email sent: %s", subject)
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Email auth failed — check EMAIL_SENDER and EMAIL_PASSWORD.")
    except smtplib.SMTPException as e:
        logger.error("SMTP error: %s", e)
    except OSError as e:
        logger.error("Network error sending email: %s", e)

    return False
