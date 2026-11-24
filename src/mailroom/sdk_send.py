"""The same send, written with the official resend SDK, for comparison.

Mailroom keeps the httpx version (see AGENTS.md). This module is only here to read side by side.
"""

import os

from mailroom.plan import SENDER, PlannedEmail
from mailroom.sending import DEFAULT_API_KEY, DEFAULT_API_URL, check_recipient, check_server


def send_with_sdk(email: PlannedEmail, key: str | None = None) -> str:
    import resend

    # The SDK reads RESEND_API_URL once, when it is imported (resend/__init__.py). Set it explicitly.
    resend.api_url = os.environ.get("RESEND_API_URL", DEFAULT_API_URL)
    resend.api_key = os.environ.get("RESEND_API_KEY", DEFAULT_API_KEY)
    check_server(resend.api_url)
    check_recipient(email.to)
    params: resend.Emails.SendParams = {"from": SENDER, "to": [email.to], "subject": email.subject, "text": email.text}
    options: resend.Emails.SendOptions = {"idempotency_key": key} if key else {}
    sent = resend.Emails.send(params, options)
    return str(sent["id"])
