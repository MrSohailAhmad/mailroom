import asyncio
import json

import httpx

from mailroom.plan import PlannedEmail
from mailroom.sending import send_all_at_once, send_all_one_by_one

EMAILS = [
    PlannedEmail(to=f"person{i}@example.com", group="tea-curious", subject="Hi", text="Hi there,\n") for i in range(24)
]


def test_one_by_one_sends_every_email_in_order() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        to = json.loads(request.content)["to"][0]
        seen.append(to)
        return httpx.Response(200, json={"id": f"id-{to}"})

    client = httpx.Client(base_url="http://localhost:4000", transport=httpx.MockTransport(handler))
    results = send_all_one_by_one(client, EMAILS, api_key="re_practice", latency=0)
    assert seen == [e.to for e in EMAILS]
    assert [r.to for r in results] == [e.to for e in EMAILS]


def test_at_once_keeps_order_and_never_runs_more_than_5() -> None:
    active = 0
    most = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal active, most
        active += 1
        most = max(most, active)
        to = json.loads(request.content)["to"][0]
        # later emails answer faster, so the finishing order differs from the plan
        await asyncio.sleep(0.02 if to.endswith("0@example.com") else 0.001)
        active -= 1
        return httpx.Response(200, json={"id": f"id-{to}"})

    async def run() -> list[str]:
        async with httpx.AsyncClient(base_url="http://localhost:4000", transport=httpx.MockTransport(handler)) as client:
            results = await send_all_at_once(client, EMAILS, api_key="re_practice", latency=0, at_once=5)
            return [r.to for r in results]

    assert asyncio.run(run()) == [e.to for e in EMAILS]
    assert 1 < most <= 5
