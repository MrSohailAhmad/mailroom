import csv
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class Subscriber:
    first_name: str
    last_name: str
    email: str
    group: str
    joined_on: date
    consent: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


def read_subscribers(path: str) -> list[Subscriber]:
    # The only place that knows the CSV column names.
    with open(path, encoding="utf-8", newline="") as file:
        return [
            Subscriber(
                first_name=row["first_name"],
                last_name=row["last_name"],
                email=row["email"],
                group=row["group"],
                joined_on=date.fromisoformat(row["joined_on"]),
                consent=row["consent"],
            )
            for row in csv.DictReader(file)
        ]


def count_by_group(subscribers: list[Subscriber]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for subscriber in subscribers:
        counts[subscriber.group] = counts.get(subscriber.group, 0) + 1
    return counts


def joined_since(subscribers: list[Subscriber], start: date, run_date: date) -> list[Subscriber]:
    return [s for s in subscribers if start <= s.joined_on <= run_date]


def joined_within_days(subscribers: list[Subscriber], days: int, run_date: date) -> list[Subscriber]:
    # "The last 30 days" includes the day exactly 30 days before the run date.
    return joined_since(subscribers, run_date - timedelta(days=days), run_date)
