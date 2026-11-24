import json
from datetime import date
from pathlib import Path

import httpx

from mailroom.issue import Issue
from mailroom.plan import build_plan
from mailroom.report import build_report, read_sent, write_sent
from mailroom.sending import SendResult, send_all_one_by_one
from mailroom.subscribers import load_subscribers


def send_everyone() -> list[SendResult]:
    def handler(request: httpx.Request) -> httpx.Response:
        to = json.loads(request.content)["to"][0]
        return httpx.Response(200, json={"id": f"id-{to}"})

    run_date = date(2026, 12, 7)
    subscribers = load_subscribers("data/subscribers.csv", run_date).good
    plan = build_plan(Issue.from_file("issues/issue-01.md"), subscribers, run_date)
    client = httpx.Client(base_url="http://localhost:4000", transport=httpx.MockTransport(handler))
    return send_all_one_by_one(client, plan.emails, "re_practice", latency=0, issue=plan.issue)


def test_report_after_sending_to_all_24_says_8_per_group_and_no_failures(tmp_path: Path) -> None:
    path = tmp_path / "sent.json"
    write_sent(send_everyone(), str(path))
    report = build_report(read_sent(str(path)))
    assert report.per_group == {"tea-curious": 8, "gift-buyers": 8, "daily-drinkers": 8}
    assert report.failures == []


def test_sent_json_has_id_recipient_and_status(tmp_path: Path) -> None:
    path = tmp_path / "sent.json"
    write_sent(send_everyone(), str(path))
    first = json.loads(path.read_text(encoding="utf-8"))["emails"][0]
    assert first == {"to": "ayesha.khan@example.com", "group": "tea-curious", "id": "id-ayesha.khan@example.com", "status": "sent", "error": None}


def test_report_lists_failures(tmp_path: Path) -> None:
    path = tmp_path / "sent.json"
    write_sent(
        [
            SendResult("a@example.com", "tea-curious", "id-1", None),
            SendResult("b@example.com", "gift-buyers", None, "The server answered 500"),
        ],
        str(path),
    )
    report = build_report(read_sent(str(path)))
    assert report.per_group == {"tea-curious": 1}
    assert [f.to for f in report.failures] == ["b@example.com"]
