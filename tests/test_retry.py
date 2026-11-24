import httpx
import pytest

from mailroom.plan import PlannedEmail
from mailroom.sending import Rejected, SendError, idempotency_key, send_with_retry

EMAIL = PlannedEmail(to="delivered@resend.dev", group="tea-curious", subject="Hi", text="Hi there,\n")


def server(answers: list[int], seen: list[httpx.Request]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        status = answers.pop(0)
        if status == 0:
            raise httpx.ConnectError("refused", request=request)
        if status == 1:
            raise httpx.ReadTimeout("slow", request=request)
        return httpx.Response(status, json={"id": "email-1", "message": f"status {status}"})

    return httpx.Client(base_url="http://localhost:4000", transport=httpx.MockTransport(handler))


def no_sleep(seconds: float) -> None:
    pass


def test_retries_after_5xx_then_succeeds() -> None:
    seen: list[httpx.Request] = []
    assert send_with_retry(server([500, 200], seen), EMAIL, "re_practice", "k1", sleep=no_sleep) == "email-1"
    assert len(seen) == 2


def test_retries_after_429_timeout_and_no_connection() -> None:
    seen: list[httpx.Request] = []
    assert send_with_retry(server([429, 1, 200], seen), EMAIL, "re_practice", "k1", sleep=no_sleep) == "email-1"
    seen2: list[httpx.Request] = []
    assert send_with_retry(server([0, 200], seen2), EMAIL, "re_practice", "k1", sleep=no_sleep) == "email-1"


def test_gives_up_after_3_tries_with_growing_waits() -> None:
    waits: list[float] = []
    seen: list[httpx.Request] = []
    with pytest.raises(SendError):
        send_with_retry(server([503, 503, 503, 200], seen), EMAIL, "re_practice", "k1", sleep=waits.append)
    assert len(seen) == 3
    assert waits == sorted(waits) and len(waits) == 2 and waits[0] < waits[1]


def test_never_retries_a_4xx() -> None:
    seen: list[httpx.Request] = []
    with pytest.raises(Rejected):
        send_with_retry(server([422, 200], seen), EMAIL, "re_practice", "k1", sleep=no_sleep)
    assert len(seen) == 1


def test_every_try_sends_the_same_idempotency_key() -> None:
    seen: list[httpx.Request] = []
    send_with_retry(server([500, 200], seen), EMAIL, "re_practice", "issue-01:delivered@resend.dev", sleep=no_sleep)
    assert {r.headers["Idempotency-Key"] for r in seen} == {"issue-01:delivered@resend.dev"}


def test_idempotency_key_comes_from_issue_and_recipient() -> None:
    assert idempotency_key("issue-01", "Ayesha.Khan@example.com") == "issue-01:ayesha.khan@example.com"


def test_409_same_key_different_body_is_not_retried() -> None:
    seen: list[httpx.Request] = []
    with pytest.raises(SendError) as error:
        send_with_retry(server([409, 200], seen), EMAIL, "re_practice", "k1", sleep=no_sleep)
    assert "409" in str(error.value)
    assert len(seen) == 1
