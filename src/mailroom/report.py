import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from mailroom.sending import SendResult


class SentEmail(BaseModel):
    to: str
    group: str
    id: str | None
    status: Literal["sent", "failed"]
    error: str | None


class SentLog(BaseModel):
    emails: list[SentEmail]


@dataclass
class Report:
    per_group: dict[str, int]
    failures: list[SentEmail]


def write_sent(results: list[SendResult], path: str) -> None:
    log = SentLog(
        emails=[
            SentEmail(
                to=r.to,
                group=r.group,
                id=r.email_id,
                status="failed" if r.error else "sent",
                error=r.error,
            )
            for r in results
        ]
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(log.model_dump_json(indent=2) + "\n", encoding="utf-8")


def read_sent(path: str) -> SentLog:
    # JSON read from a file goes through a model too.
    return SentLog.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))


def build_report(log: SentLog) -> Report:
    per_group: dict[str, int] = {}
    failures: list[SentEmail] = []
    for email in log.emails:
        if email.status == "sent":
            per_group[email.group] = per_group.get(email.group, 0) + 1
        else:
            failures.append(email)
    return Report(per_group, failures)
