from datetime import date

from mailroom.send_dates import next_send_date
from mailroom.subscribers import count_by_group, joined_since, joined_within_days, read_subscribers

SUBSCRIBERS = read_subscribers("data/subscribers.csv")


def test_counts_all_24_subscribers() -> None:
    assert len(SUBSCRIBERS) == 24


def test_counts_8_tea_curious() -> None:
    assert count_by_group(SUBSCRIBERS)["tea-curious"] == 8


def test_counts_8_gift_buyers() -> None:
    assert count_by_group(SUBSCRIBERS)["gift-buyers"] == 8


def test_counts_8_daily_drinkers() -> None:
    assert count_by_group(SUBSCRIBERS)["daily-drinkers"] == 8


def test_all_24_gave_consent() -> None:
    assert sum(1 for s in SUBSCRIBERS if s.consent != "") == 24


def test_7_joined_in_last_30_days() -> None:
    assert len(joined_within_days(SUBSCRIBERS, 30, date(2026, 11, 20))) == 7


def test_joined_exactly_30_days_ago_counts() -> None:
    names = [s.first_name for s in joined_within_days(SUBSCRIBERS, 30, date(2026, 11, 20))]
    assert "Amara" in names


def test_next_send_after_20_november_is_7_december() -> None:
    assert next_send_date(date(2026, 11, 20)) == date(2026, 12, 7)


def test_next_send_after_7_december_is_4_january() -> None:
    assert next_send_date(date(2026, 12, 7)) == date(2027, 1, 4)


def test_next_send_after_31_december_is_4_january() -> None:
    assert next_send_date(date(2026, 12, 31)) == date(2027, 1, 4)


def test_12_joined_since_1_october() -> None:
    assert len(joined_since(SUBSCRIBERS, date(2026, 10, 1), date(2026, 11, 20))) == 12


def test_run_date_must_be_a_date_not_text() -> None:
    # Was called with the text "2026-11-20": a TypeError at run time, and pyright flags it.
    assert len(joined_within_days(SUBSCRIBERS, 30, date.fromisoformat("2026-11-20"))) == 7
