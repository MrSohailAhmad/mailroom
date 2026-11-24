import argparse
import asyncio
import sys
import time
from datetime import date
from pathlib import Path

from mailroom.checks import check_issue
from mailroom.issue import Issue
from mailroom.report import build_report, read_sent, write_sent
from mailroom.plan import PlannedEmail, body_without_headers, build_plan, write_plan
import httpx

from mailroom.sending import (
    SendError,
    SendRefused,
    SendResult,
    api_key,
    api_url,
    check_server,
    get_email,
    make_client,
    send_all_at_once,
    send_all_one_by_one,
    send_one,
)
from mailroom.send_dates import next_send_date
from mailroom.subscribers import (
    DataFileError,
    LoadResult,
    count_by_group,
    joined_since,
    joined_within_days,
    load_subscribers,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mailroom", description="Kettlebird Tea Steep Club newsletter tool.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_subs = sub.add_parser("subscribers", help="count subscribers")
    p_subs.add_argument("file", nargs="?", default="data/subscribers.csv")
    p_subs.add_argument("--since-days", type=int)
    p_subs.add_argument("--since", type=date.fromisoformat)
    p_subs.add_argument("--run-date", type=date.fromisoformat)

    p_check = sub.add_parser("check", help="check an issue against the rules")
    p_check.add_argument("issue")

    p_import = sub.add_parser("import", help="check new sign-ups through the model and our rules")
    p_import.add_argument("file")
    p_import.add_argument("--run-date", type=date.fromisoformat)

    p_send = sub.add_parser("send", help="send an issue to every subscriber")
    p_send.add_argument("issue")
    p_send.add_argument("--dry-run", action="store_true", help="only write outbox/plan.json")
    p_send.add_argument("--run-date", type=date.fromisoformat)
    p_send.add_argument("--subscribers", default="data/subscribers.csv")
    p_send.add_argument("--outbox", default="outbox")
    p_send.add_argument("--latency", type=float, default=0.0, help="seconds to wait before each request")
    p_send.add_argument("--at-once", type=int, help="send this many at the same time")

    p_one = sub.add_parser("send-one", help="send one email to the practice server")
    p_one.add_argument("issue")
    p_one.add_argument("--to", required=True)

    p_report = sub.add_parser("report", help="how many emails each group got, and any failures")
    p_report.add_argument("--outbox", default="outbox")

    p_next = sub.add_parser("next-send", help="date of the next send")
    p_next.add_argument("--run-date", type=date.fromisoformat)
    return parser


def send_plan(emails: list[PlannedEmail], latency: float, at_once: int | None, issue: str) -> list[SendResult]:
    if at_once is None:
        with make_client() as client:
            return send_all_one_by_one(client, emails, api_key(), latency, issue)

    async def go() -> list[SendResult]:
        url = api_url()
        check_server(url)
        async with httpx.AsyncClient(base_url=url, timeout=10.0) as client:
            return await send_all_at_once(client, emails, api_key(), latency, at_once, issue)

    return asyncio.run(go())


def print_problems(result: LoadResult) -> None:
    for problem in result.problems:
        print(problem)


def main() -> None:
    args = build_parser().parse_args()

    # The only place that reads today's date.
    run_date: date = getattr(args, "run_date", None) or date.today()

    try:
        run(args, run_date)
    except (DataFileError, SendRefused) as error:
        print(error, file=sys.stderr)
        sys.exit(2)
    except SendError as error:
        print(error, file=sys.stderr)
        sys.exit(1)


def run(args: argparse.Namespace, run_date: date) -> None:
    if args.command == "subscribers":
        result = load_subscribers(args.file, run_date)
        subscribers = result.good
        if args.since_days is not None:
            subscribers = joined_within_days(subscribers, args.since_days, run_date)
        elif args.since is not None:
            subscribers = joined_since(subscribers, args.since, run_date)
        print(f"Total: {len(subscribers)}")
        for group, count in count_by_group(subscribers).items():
            print(f"{group}: {count}")
        consented = sum(1 for s in subscribers if s.consent != "")
        print(f"Gave consent: {consented}")
        print_problems(result)
        if result.problems:
            sys.exit(1)
    elif args.command == "check":
        problems = check_issue(Issue.from_file(args.issue))
        if problems:
            for problem in problems:
                print(problem)
            sys.exit(1)
        print("OK")
    elif args.command == "import":
        result = load_subscribers(args.file, run_date)
        for subscriber in result.good:
            print(f"accepted: {subscriber.full_name}")
        print_problems(result)
        if result.problems:
            sys.exit(1)
    elif args.command == "send":
        issue = Issue.from_file(args.issue)
        problems = check_issue(issue)
        if problems:
            for problem in problems:
                print(problem)
            print("The issue failed the check, so nothing was planned or sent.")
            sys.exit(1)
        result = load_subscribers(args.subscribers, run_date)
        if result.problems:
            print_problems(result)
            sys.exit(1)
        plan = build_plan(issue, result.good, run_date, Path(args.issue).stem)
        plan_path = str(Path(args.outbox) / "plan.json")
        write_plan(plan, plan_path)
        print(f"Planned {len(plan.emails)} emails -> {plan_path}")
        if not args.dry_run:
            started = time.perf_counter()
            results = send_plan(plan.emails, args.latency, args.at_once, plan.issue)
            took = time.perf_counter() - started
            write_sent(results, str(Path(args.outbox) / "sent.json"))
            failures = [r for r in results if r.error]
            print(f"Sent {len(results) - len(failures)} of {len(results)} in {took:.1f} seconds")
            for failure in failures:
                print(f"failed: {failure.to}: {failure.error}")
            if failures:
                sys.exit(1)
    elif args.command == "send-one":
        issue = Issue.from_file(args.issue)
        problems = check_issue(issue)
        if problems:
            for problem in problems:
                print(problem)
            sys.exit(1)
        text = issue.personalize("there")
        email = PlannedEmail(to=args.to, group="practice", subject=issue.subject or "", text=body_without_headers(text))
        with make_client() as client:
            email_id = send_one(client, email, api_key())
            print(f"Sent: 200 id={email_id}")
            status = get_email(client, email_id, api_key())
            print(f"Status: {status.get('last_event', 'unknown')}")
    elif args.command == "report":
        sent_path = Path(args.outbox) / "sent.json"
        if not sent_path.exists():
            raise DataFileError(f"{sent_path} does not exist: run mailroom send first.")
        report = build_report(read_sent(str(sent_path)))
        for group, count in report.per_group.items():
            print(f"{group}: {count}")
        print(f"Failures: {len(report.failures)}")
        for failure in report.failures:
            print(f"failed: {failure.to}: {failure.error}")
        if report.failures:
            sys.exit(1)
    elif args.command == "next-send":
        print(f"Next send: {next_send_date(run_date).isoformat()}")
