import csv
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, ValidationError

Group = Literal["tea-curious", "gift-buyers", "daily-drinkers"]


class Subscriber(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    group: Group
    joined_on: date
    consent: str = Field(min_length=1)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


COLUMNS = ["first_name", "last_name", "email", "group", "joined_on", "consent"]


class DataFileError(Exception):
    """A problem with the whole file: stop everything."""


@dataclass
class Problem:
    row: int
    field: str
    message: str

    def __str__(self) -> str:
        return f"row {self.row}, {self.field}: {self.message}"


@dataclass
class LoadResult:
    good: list[Subscriber]
    problems: list[Problem]


def reason(error: ValidationError) -> str:
    parts: list[str] = []
    for item in error.errors():
        field = ".".join(str(part) for part in item["loc"])
        parts.append(f"{field}: {item['msg']}")
    return "; ".join(parts)


def read_rows(path: str) -> list[dict[str, str]]:
    try:
        with open(path, encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != COLUMNS:
                raise DataFileError(f"{path} has the wrong columns: expected {','.join(COLUMNS)}.")
            return list(reader)
    except FileNotFoundError:
        raise DataFileError(f"{path} does not exist.") from None


def import_rows(path: str) -> tuple[list[Subscriber], list[tuple[str, str]]]:
    """Read a CSV through the model. Returns (accepted, [(first_name, reason)])."""
    accepted: list[Subscriber] = []
    rejected: list[tuple[str, str]] = []
    for row in read_rows(path):
        try:
            accepted.append(Subscriber.model_validate(row))
        except ValidationError as error:
            rejected.append((row.get("first_name") or "?", reason(error)))
    return accepted, rejected


ALLOWED_DOMAIN = "@example.com"


def apply_our_rules(
    subscribers: list[Subscriber], run_date: date
) -> tuple[list[Subscriber], list[tuple[Subscriber, str]]]:
    """The model checks the shape. These rules check the meaning.

    The date rule needs the run date, which the model does not have, so it lives here.
    """
    kept: list[Subscriber] = []
    broken: list[tuple[Subscriber, str]] = []
    for subscriber in subscribers:
        if not subscriber.email.lower().endswith(ALLOWED_DOMAIN):
            broken.append((subscriber, f"email: must end in {ALLOWED_DOMAIN}"))
        elif subscriber.joined_on > run_date:
            broken.append((subscriber, f"joined_on: {subscriber.joined_on} is after the run date {run_date}"))
        else:
            kept.append(subscriber)
    return kept, broken


def load_subscribers(path: str, run_date: date) -> LoadResult:
    """Return the good subscribers and every problem, each with its row and field.

    Row numbers are file lines: the header is row 1, so the first person is row 2.
    """
    good: list[Subscriber] = []
    problems: list[Problem] = []
    for row_number, row in enumerate(read_rows(path), start=2):
        try:
            subscriber = Subscriber.model_validate(row)
        except ValidationError as error:
            for item in error.errors():
                field = ".".join(str(part) for part in item["loc"])
                problems.append(Problem(row_number, field, item["msg"]))
            continue
        kept, broken = apply_our_rules([subscriber], run_date)
        good += kept
        for _, why in broken:
            field, message = why.split(": ", 1)
            problems.append(Problem(row_number, field, message))
    return LoadResult(good, problems)


def read_subscribers(path: str) -> list[Subscriber]:
    accepted, _ = import_rows(path)
    return accepted


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
