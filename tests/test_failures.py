import httpx
import pytest

from mailroom.plan import PlannedEmail
from mailroom.sending import NotFound, Rejected, ServerDown, Unauthorized, get_email, send_one

EMAIL = PlannedEmail(to="delivered@resend.dev", group="tea-curious", subject="Hi", text="Hi there,\n")


def server(status: int, body: dict[str, object], calls: list[int]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(status, json=body)

    return httpx.Client(base_url="http://localhost:4000", transport=httpx.MockTransport(handler))


def test_422_shows_server_message_and_is_not_retried() -> None:
    calls: list[int] = []
    body: dict[str, object] = {"statusCode": 422, "name": "validation_error", "message": "Missing `subject` field."}
    with pytest.raises(Rejected) as error:
        send_one(server(422, body, calls), EMAIL, api_key="re_practice")
    assert "Missing `subject` field." in str(error.value)
    assert calls == [1]


def test_404_says_the_id_is_unknown() -> None:
    body: dict[str, object] = {"statusCode": 404, "name": "not_found", "message": "Email not found"}
    with pytest.raises(NotFound) as error:
        get_email(server(404, body, []), "does-not-exist", api_key="re_practice")
    assert "does-not-exist" in str(error.value)


def test_401_says_the_key_is_wrong() -> None:
    body: dict[str, object] = {"statusCode": 401, "name": "missing_api_key", "message": "Missing API key"}
    with pytest.raises(Unauthorized):
        send_one(server(401, body, []), EMAIL, api_key="re_wrong")


def test_no_connection_says_start_the_practice_server() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    client = httpx.Client(base_url="http://localhost:4999", transport=httpx.MockTransport(handler))
    with pytest.raises(ServerDown) as error:
        send_one(client, EMAIL, api_key="re_practice")
    assert "npx emulate@0.12.3 start --service resend" in str(error.value)
