import csv
from datetime import date, timedelta


def read_subscribers(path: str) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def count_by_group(subscribers: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for subscriber in subscribers:
        group = subscriber["group"]
        counts[group] = counts.get(group, 0) + 1
    return counts


def joined_on(subscriber: dict[str, str]) -> date:
    return date.fromisoformat(subscriber["joined_on"])


def joined_since(subscribers: list[dict[str, str]], start: date, run_date: date) -> list[dict[str, str]]:
    return [s for s in subscribers if start <= joined_on(s) <= run_date]


def joined_within_days(subscribers: list[dict[str, str]], days: int, run_date: date) -> list[dict[str, str]]:
    # "The last 30 days" includes the day exactly 30 days before the run date.
    return joined_since(subscribers, run_date - timedelta(days=days), run_date)
