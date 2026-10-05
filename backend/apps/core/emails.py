from django.core import signing
from django.template.loader import render_to_string

from .tasks import dispatch, send_email

UNSUBSCRIBE_SALT = "newsletter-unsubscribe"


def send_templated_email(template: str, context: dict, to: list[str], subject: str) -> None:
    """Render `emails/<template>.txt` now and send it in the background, so a slow mail server never stalls the request."""
    body = render_to_string(f"emails/{template}.txt", context)
    dispatch(send_email, subject, body, list(to))


def make_unsubscribe_token(email: str) -> str:
    return signing.dumps(email.lower(), salt=UNSUBSCRIBE_SALT)


def check_unsubscribe_token(email: str, token: str) -> bool:
    try:
        return signing.loads(token, salt=UNSUBSCRIBE_SALT) == email.lower()
    except signing.BadSignature:
        return False
