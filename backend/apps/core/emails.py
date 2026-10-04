import logging
import threading

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

UNSUBSCRIBE_SALT = "newsletter-unsubscribe"


def send_templated_email(template: str, context: dict, to: list[str], subject: str) -> None:
    """Render `emails/<template>.txt` and send it; failures are logged, never raised to the request."""
    body = render_to_string(f"emails/{template}.txt", context)

    def _send():
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, to)
        except Exception:  # noqa: BLE001 - email must not break the user flow
            logger.exception("Failed to send '%s' email to %s", template, to)

    # Sent in the background so a slow or blocked mail server never stalls the request.
    threading.Thread(target=_send, daemon=True).start()


def make_unsubscribe_token(email: str) -> str:
    return signing.dumps(email.lower(), salt=UNSUBSCRIBE_SALT)


def check_unsubscribe_token(email: str, token: str) -> bool:
    try:
        return signing.loads(token, salt=UNSUBSCRIBE_SALT) == email.lower()
    except signing.BadSignature:
        return False
