import json

import httpx
import pytest

from mailroom.plan import PlannedEmail
from mailroom.sending import SendRefused, check_recipient, check_server, get_email, send_one

EMAIL = PlannedEmail(to="delivered@resend.dev", group="tea-curious", subject="The Steep Club opens Monday", text="Hi there,\n")


def fake_server(seen: list[httpx.Request]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "POST":
            return httpx.Response(200, json={"id": "email-123"})
        return httpx.Response(200, json={"id": "email-123", "last_event": "delivered"})

    return httpx.Client(base_url="http://localhost:4000", transport=httpx.MockTransport(handler))


def test_send_posts_to_emails_with_bearer_key_and_body() -> None:
    seen: list[httpx.Request] = []
    email_id = send_one(fake_server(seen), EMAIL, api_key="re_practice")
    assert email_id == "email-123"
    request = seen[0]
    assert request.method == "POST"
    assert request.url.path == "/emails"
    assert request.headers["Authorization"] == "Bearer re_practice"
    body = json.loads(request.content)
    assert body == {"from": "onboarding@resend.dev", "to": ["delivered@resend.dev"], "subject": EMAIL.subject, "text": EMAIL.text}


def test_get_email_reads_status() -> None:
    assert get_email(fake_server([]), "email-123", api_key="re_practice")["last_event"] == "delivered"


def test_gmail_is_refused_before_any_request() -> None:
    seen: list[httpx.Request] = []
    gmail = EMAIL.model_copy(update={"to": "sara.ali@gmail.com"})
    with pytest.raises(SendRefused):
        send_one(fake_server(seen), gmail, api_key="re_practice")
    assert seen == []


def test_example_and_resend_dev_recipients_are_allowed() -> None:
    check_recipient("ayesha.khan@example.com")
    check_recipient("delivered@resend.dev")


def test_real_service_is_refused() -> None:
    with pytest.raises(SendRefused):
        check_server("https://api.resend.com")


def test_localhost_is_allowed() -> None:
    check_server("http://localhost:4000")
    check_server("http://127.0.0.1:4000")
