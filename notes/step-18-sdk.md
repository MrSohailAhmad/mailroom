# Step 18: reading the resend SDK (resend 2.55.0)

Side by side: `src/mailroom/sending.py` (`send_one`, httpx) and `src/mailroom/sdk_send.py` (`send_with_sdk`, the SDK).

Where things happen in the SDK source (`.venv/lib/python3.13/site-packages/resend/`):
- **Base URL**: `__init__.py:160` – `api_url = os.environ.get("RESEND_API_URL", "https://api.resend.com")`, read once at import.
- **Builds the request**: `request.py:41` – `perform()` calls `make_request(url=f"{resend.api_url}{self.path}")`; headers in `__get_headers()` at `request.py:77` (Bearer key, and `Idempotency-Key` when `idempotency_key` is in the options, `request.py:85`).
- **Error becomes an exception**: `request.py:52` – a status of 400+ calls `raise_for_code_and_type()` (`exceptions.py:229`), which picks ValidationError, RateLimitError, etc.
- **Timeout**: `http_client_requests.py:13` – `RequestsClient(timeout=30)`, 30 seconds by default (the default client, `__init__.py:151`).
- **Retries**: none. No retry code anywhere; a network failure becomes `RuntimeError("Request failed: ...")` at `http_client_requests.py:33`. The word "retry" only appears in an error message's suggested action.

So the SDK builds the request and turns errors into exceptions; retrying and idempotency are left to us.

Our retry (`send_with_retry`): at most 3 tries, waits 0.5 s then 1 s, only after no connection, a timeout, a 429 or a 5xx. Never a 4xx (422, 404, 401, 409 fail at once). Every send carries an idempotency key, `<issue>:<recipient>`, the same on every try.

Decision: Mailroom keeps **httpx**. It already has our two guards, our own error messages, async sending with a limit, and retries we control. The SDK would add a second HTTP library (requests) and hides the status code behind its own exceptions.
