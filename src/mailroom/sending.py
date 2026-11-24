import os
from typing import Any
from urllib.parse import urlparse

import httpx

from mailroom.plan import SENDER, PlannedEmail

DEFAULT_API_URL = "http://localhost:4000"
DEFAULT_API_KEY = "re_practice"
ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
ALLOWED_RECIPIENT_DOMAINS = ("@example.com", "@resend.dev")


class SendRefused(Exception):
    """Mailroom refused to send, before any request was made."""


def api_url() -> str:
    return os.environ.get("RESEND_API_URL", DEFAULT_API_URL)


def api_key() -> str:
    return os.environ.get("RESEND_API_KEY", DEFAULT_API_KEY)


def check_server(url: str) -> None:
    if urlparse(url).hostname not in ALLOWED_HOSTS:
        raise SendRefused(f"Refusing to send to {url}: sending works only against localhost.")


def check_recipient(address: str) -> None:
    if not address.lower().endswith(ALLOWED_RECIPIENT_DOMAINS):
        raise SendRefused(f"Refusing to send to {address}: only @example.com and @resend.dev addresses are allowed.")


def make_client() -> httpx.Client:
    url = api_url()
    check_server(url)
    return httpx.Client(base_url=url, timeout=10.0)


def send_one(client: httpx.Client, email: PlannedEmail, api_key: str) -> str:
    check_server(str(client.base_url))
    check_recipient(email.to)
    body = {"from": SENDER, "to": [email.to], "subject": email.subject, "text": email.text}
    response = client.post("/emails", json=body, headers={"Authorization": f"Bearer {api_key}"})
    response.raise_for_status()
    return str(response.json()["id"])


def get_email(client: httpx.Client, email_id: str, api_key: str) -> dict[str, Any]:
    response = client.get(f"/emails/{email_id}", headers={"Authorization": f"Bearer {api_key}"})
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    return data
