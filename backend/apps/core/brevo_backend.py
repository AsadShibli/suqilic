"""Email backend that sends through Brevo's HTTPS API.

Free hosts (e.g. Render) block outgoing SMTP ports, but HTTPS works. Set
EMAIL_BACKEND=apps.core.brevo_backend.BrevoEmailBackend and BREVO_API_KEY.
"""

import json
import logging
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)
API_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for m in email_messages:
            name, addr = parseaddr(m.from_email or settings.DEFAULT_FROM_EMAIL)
            payload = {
                "sender": {"email": addr, **({"name": name} if name else {})},
                "to": [{"email": t} for t in m.to],
                "subject": m.subject,
                "textContent": m.body,
            }
            req = urllib.request.Request(
                API_URL,
                data=json.dumps(payload).encode(),
                headers={"api-key": settings.BREVO_API_KEY, "content-type": "application/json", "accept": "application/json"},
            )
            try:
                urllib.request.urlopen(req, timeout=10).read()
                sent += 1
            except Exception:  # noqa: BLE001
                logger.exception("Brevo send failed")
                if not self.fail_silently:
                    raise
        return sent
