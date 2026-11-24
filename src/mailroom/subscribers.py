import csv
from datetime import date, timedelta


def read_subscribers(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def count_by_group(subscribers):
    counts = {}
    for subscriber in subscribers:
        group = subscriber["group"]
        counts[group] = counts.get(group, 0) + 1
    return counts


def joined_on(subscriber):
    return date.fromisoformat(subscriber["joined_on"])


def joined_since(subscribers, start, run_date):
    return [s for s in subscribers if start <= joined_on(s) <= run_date]


def joined_within_days(subscribers, days, run_date):
    # "The last 30 days" includes the day exactly 30 days before the run date.
    return joined_since(subscribers, run_date - timedelta(days=days), run_date)
