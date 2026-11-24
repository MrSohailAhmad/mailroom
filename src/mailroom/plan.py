import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, EmailStr, Field

from mailroom.issue import Issue
from mailroom.subscribers import Subscriber

SENDER = "onboarding@resend.dev"
COMPANY_ADDRESS = "12 Leaf Lane, Portland, OR 97201"
UNSUBSCRIBE_URL = "https://kettlebird.example/unsubscribe"


class PlannedEmail(BaseModel):
    to: EmailStr
    group: str
    subject: str = Field(min_length=1, max_length=50)
    text: str = Field(min_length=1)


class Plan(BaseModel):
    issue: str
    run_date: date
    emails: list[PlannedEmail]


def fill(issue: Issue, subscriber: Subscriber) -> str:
    text = issue.personalize(subscriber.first_name)
    text = text.replace("{{company_address}}", COMPANY_ADDRESS)
    return text.replace("{{unsubscribe_url}}", UNSUBSCRIBE_URL)


def body_without_headers(text: str) -> str:
    lines = text.splitlines()
    return "\n".join(line for line in lines if not line.startswith(("Subject:", "Preview:"))).strip() + "\n"


def build_plan(issue: Issue, subscribers: list[Subscriber], run_date: date, issue_name: str = "issue-01") -> Plan:
    emails = [
        PlannedEmail(
            to=subscriber.email,
            group=subscriber.group,
            subject=issue.subject or "",
            text=body_without_headers(fill(issue, subscriber)),
        )
        for subscriber in subscribers
    ]
    return Plan(issue=issue_name, run_date=run_date, emails=emails)


def write_plan(plan: Plan, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")


def read_plan(path: str) -> Plan:
    # JSON read from a file is outside data: it goes through the model too.
    return Plan.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))
