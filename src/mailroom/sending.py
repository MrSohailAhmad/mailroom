import asyncio
import os
import time
from dataclasses import dataclass
from collections.abc import Callable
from typing import cast
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
    """No connection: the practice server is not running. Worth retrying."""


class TimedOut(SendError):
    """The server did not answer in time. Worth retrying."""


class TryLater(SendError):
    """429 or 5xx: the server may succeed later. Worth retrying."""


RETRYABLE = (ServerDown, TimedOut, TryLater)
MAX_TRIES = 3
FIRST_WAIT = 0.5


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
    if response.status_code == 409:
        raise SendError(f"Same idempotency key with a different email (409): {message}")
    if response.status_code == 429 or response.status_code >= 500:
        raise TryLater(f"The server answered {response.status_code}, try again later: {message}")
    raise SendError(f"The server answered {response.status_code}: {message}")


def headers_for(api_key: str, key: str | None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {api_key}"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


def request(
    client: httpx.Client,
    method: str,
    path: str,
    api_key: str,
    json: dict[str, object] | None = None,
    key: str | None = None,
) -> httpx.Response:
    try:
        return client.request(method, path, headers=headers_for(api_key, key), json=json)
    except httpx.ConnectError:
        raise ServerDown(f"The practice server at {client.base_url} is not running. {START_SERVER}") from None
    except httpx.TimeoutException:
        raise TimedOut(f"The server at {client.base_url} did not answer in time.") from None


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


def email_body(email: PlannedEmail) -> dict[str, object]:
    return {"from": SENDER, "to": [email.to], "subject": email.subject, "text": email.text}


def idempotency_key(issue: str, recipient: str) -> str:
    return f"{issue}:{recipient.lower()}"


def send_one(client: httpx.Client, email: PlannedEmail, api_key: str, key: str | None = None) -> str:
    check_server(str(client.base_url))
    check_recipient(email.to)
    body = email_body(email)
    response = request(client, "POST", "/emails", api_key, json=body, key=key)
    raise_for(response, email.to)
    return str(response.json()["id"])


def get_email(client: httpx.Client, email_id: str, api_key: str) -> dict[str, object]:
    response = request(client, "GET", f"/emails/{email_id}", api_key)
    raise_for(response, email_id)
    return cast(dict[str, object], response.json())


def send_with_retry(
    client: httpx.Client,
    email: PlannedEmail,
    api_key: str,
    key: str,
    sleep: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] | None = None,
) -> str:
    """Retry only what can succeed later: no connection, a timeout, a 429 or a 5xx. Never a 4xx."""
    wait = FIRST_WAIT
    for attempt in range(1, MAX_TRIES + 1):
        try:
            return send_one(client, email, api_key, key)
        except RETRYABLE as error:
            if attempt == MAX_TRIES:
                raise
            if log is not None:
                log(f"try {attempt} failed ({error}); waiting {wait:.1f}s")
            sleep(wait)
            wait *= 2
    raise AssertionError("unreachable")


@dataclass
class SendResult:
    to: str
    group: str
    email_id: str | None
    error: str | None


def send_all_one_by_one(
    client: httpx.Client, emails: list[PlannedEmail], api_key: str, latency: float, issue: str = "issue"
) -> list[SendResult]:
    results: list[SendResult] = []
    for email in emails:
        time.sleep(latency)  # stands in for the internet
        try:
            email_id = send_with_retry(client, email, api_key, idempotency_key(issue, email.to))
            results.append(SendResult(email.to, email.group, email_id, None))
        except SendError as error:
            results.append(SendResult(email.to, email.group, None, str(error)))
    return results


async def send_one_async(client: httpx.AsyncClient, email: PlannedEmail, api_key: str, key: str) -> str:
    check_server(str(client.base_url))
    check_recipient(email.to)
    try:
        response = await client.post("/emails", json=email_body(email), headers=headers_for(api_key, key))
    except httpx.ConnectError:
        raise ServerDown(f"The practice server at {client.base_url} is not running. {START_SERVER}") from None
    except httpx.TimeoutException:
        raise TimedOut(f"The server at {client.base_url} did not answer in time.") from None
    raise_for(response, email.to)
    return str(response.json()["id"])


async def send_with_retry_async(client: httpx.AsyncClient, email: PlannedEmail, api_key: str, key: str) -> str:
    wait = FIRST_WAIT
    for attempt in range(1, MAX_TRIES + 1):
        try:
            return await send_one_async(client, email, api_key, key)
        except RETRYABLE:
            if attempt == MAX_TRIES:
                raise
            await asyncio.sleep(wait)
            wait *= 2
    raise AssertionError("unreachable")


async def send_all_at_once(
    client: httpx.AsyncClient,
    emails: list[PlannedEmail],
    api_key: str,
    latency: float,
    at_once: int,
    issue: str = "issue",
) -> list[SendResult]:
    limit = asyncio.Semaphore(at_once)

    async def send(email: PlannedEmail) -> SendResult:
        async with limit:
            await asyncio.sleep(latency)  # stands in for the internet
            try:
                key = idempotency_key(issue, email.to)
                return SendResult(email.to, email.group, await send_with_retry_async(client, email, api_key, key), None)
            except SendError as error:
                return SendResult(email.to, email.group, None, str(error))

    # gather returns results in the order the tasks were given: the plan's order.
    return list(await asyncio.gather(*(send(email) for email in emails)))
