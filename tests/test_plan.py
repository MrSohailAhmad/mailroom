import json
import subprocess
from datetime import date
from pathlib import Path

from mailroom.issue import Issue
from mailroom.plan import build_plan, read_plan, write_plan
from mailroom.subscribers import load_subscribers

RUN_DATE = date(2026, 12, 7)


def make_plan() -> list[dict[str, str]]:
    subscribers = load_subscribers("data/subscribers.csv", RUN_DATE).good
    plan = build_plan(Issue.from_file("issues/issue-01.md"), subscribers, RUN_DATE)
    return [entry.model_dump(mode="json") for entry in plan.emails]


def test_plan_has_24_entries() -> None:
    assert len(make_plan()) == 24


def test_first_entry_is_ayesha_greeted_by_name() -> None:
    first = make_plan()[0]
    assert first["to"] == "ayesha.khan@example.com"
    assert "Hi Ayesha" in first["text"]


def test_no_placeholder_left_unfilled() -> None:
    assert all("{{" not in entry["text"] for entry in make_plan())


def test_plan_fills_address_and_unsubscribe_link() -> None:
    text = make_plan()[0]["text"]
    assert "12 Leaf Lane, Portland, OR 97201" in text
    assert "https://kettlebird.example/unsubscribe" in text


def test_plan_round_trips_through_the_model(tmp_path: Path) -> None:
    subscribers = load_subscribers("data/subscribers.csv", RUN_DATE).good
    plan = build_plan(Issue.from_file("issues/issue-01.md"), subscribers, RUN_DATE)
    path = tmp_path / "plan.json"
    write_plan(plan, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["run_date"] == "2026-12-07"
    assert read_plan(str(path)) == plan


def test_issue_that_fails_the_check_writes_no_plan(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("Subject: \nPreview: x\n\nHello\n", encoding="utf-8")
    out = tmp_path / "outbox"
    result = subprocess.run(
        ["uv", "run", "mailroom", "send", str(bad), "--dry-run", "--run-date", "2026-12-07", "--outbox", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert not (out / "plan.json").exists()
