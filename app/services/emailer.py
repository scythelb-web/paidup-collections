"""Email service — SendGrid integration for invoice reminders."""
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, TrackingSettings, OpenTracking, ClickTracking

from app.config import SENDGRID_API_KEY

logger = logging.getLogger(__name__)


def send_reminder_email(
    to_email: str,
    to_name: str,
    subject: str,
    body_html: str,
) -> bool:
    """Send a reminder email via SendGrid with open/click tracking."""
    if not SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured")
        return False

    try:
        message = Mail(
            from_email="billing@paidup.io",
            to_emails=to_email,
            subject=subject,
            html_content=body_html,
        )

        tracking = TrackingSettings()
        tracking.open_tracking = OpenTracking(enable=True)
        tracking.click_tracking = ClickTracking(enable=True)
        message.tracking_settings = tracking

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"Email sent to {to_email}: {response.status_code}")
        return response.status_code in (200, 201, 202)
    except Exception as e:
        logger.error(f"SendGrid error: {e}")
        return False
