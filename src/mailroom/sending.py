import os
from typing import Any, cast
from urllib.parse import urlparse

import httpx

from mailroom.plan import SENDER, PlannedEmail

DEFAULT_API_URL = "http://localhost:4000"
DEFAULT_API_KEY = "re_practice"
ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
ALLOWED_RECIPIENT_DOMAINS = ("@example.com", "@resend.dev")


class SendRefused(Exception):
    """Mailroom refused to send, before any request was made."""


class SendError(Exception):
    """The server or the network said no."""


class Rejected(SendError):
    """422: the server rejected the email. Never retried."""


class NotFound(SendError):
    """404: the server does not know this id."""


class Unauthorized(SendError):
    """401: the key is missing or wrong."""


class ServerDown(SendError):
    """No connection: the practice server is not running."""


START_SERVER = "Start it in a second terminal with: npx emulate@0.12.3 start --service resend"


def server_message(response: httpx.Response) -> str:
    try:
        data: object = response.json()
    except ValueError:
        return response.text
    if isinstance(data, dict):
        message = cast(dict[str, object], data).get("message")
        if message is not None:
            return str(message)
    return response.text


def raise_for(response: httpx.Response, what: str) -> None:
    if response.is_success:
        return
    message = server_message(response)
    if response.status_code == 422:
        raise Rejected(f"The server rejected the email (422): {message}")
    if response.status_code == 404:
        raise NotFound(f"Unknown id: {what} (404)")
    if response.status_code == 401:
        raise Unauthorized(f"The API key is missing or wrong (401): {message}")
    raise SendError(f"The server answered {response.status_code}: {message}")


def request(client: httpx.Client, method: str, path: str, api_key: str, **kwargs: Any) -> httpx.Response:
    try:
        return client.request(method, path, headers={"Authorization": f"Bearer {api_key}"}, **kwargs)
    except httpx.ConnectError:
        raise ServerDown(f"The practice server at {client.base_url} is not running. {START_SERVER}") from None


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
    response = request(client, "POST", "/emails", api_key, json=body)
    raise_for(response, email.to)
    return str(response.json()["id"])


def get_email(client: httpx.Client, email_id: str, api_key: str) -> dict[str, Any]:
    response = request(client, "GET", f"/emails/{email_id}", api_key)
    raise_for(response, email_id)
    data: dict[str, Any] = response.json()
    return data
