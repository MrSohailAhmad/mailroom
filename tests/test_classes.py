from datetime import date

from mailroom.issue import Issue
from mailroom.subscribers import Subscriber, read_subscribers


def test_issue_01_has_one_link_to_the_steep_club() -> None:
    issue = Issue.from_file("issues/issue-01.md")
    assert issue.links == ["https://kettlebird.example/steep-club"]


def test_personalize_fills_first_name_and_keeps_unsubscribe() -> None:
    text = Issue.from_file("issues/issue-01.md").personalize("Ayesha")
    assert "Hi Ayesha," in text
    assert "{{first_name}}" not in text
    assert "{{unsubscribe_url}}" in text


def test_issue_knows_subject_and_preview() -> None:
    issue = Issue.from_file("issues/issue-01.md")
    assert issue.subject == "The Steep Club opens Monday"
    assert issue.preview is not None and issue.preview.startswith("Your monthly tea box")


def test_subscriber_full_name() -> None:
    first = read_subscribers("data/subscribers.csv")[0]
    assert first.full_name == "Ayesha Khan"


def test_subscriber_joined_on_is_a_date() -> None:
    first = read_subscribers("data/subscribers.csv")[0]
    assert isinstance(first, Subscriber)
    assert first.joined_on == date(2026, 9, 14)
