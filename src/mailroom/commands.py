import argparse
import sys
from datetime import date

from mailroom.checks import check_issue
from mailroom.issue import Issue
from mailroom.send_dates import next_send_date
from mailroom.subscribers import count_by_group, import_rows, joined_since, joined_within_days, read_subscribers


def main() -> None:
    parser = argparse.ArgumentParser(prog="mailroom")
    sub = parser.add_subparsers(dest="command", required=True)
    p_subs = sub.add_parser("subscribers", help="count subscribers")
    p_subs.add_argument("file", nargs="?", default="data/subscribers.csv")
    p_subs.add_argument("--since-days", type=int)
    p_subs.add_argument("--since", type=date.fromisoformat)
    p_subs.add_argument("--run-date", type=date.fromisoformat)
    p_check = sub.add_parser("check", help="check an issue against the rules")
    p_check.add_argument("issue")
    p_import = sub.add_parser("import", help="check new sign-ups through the model")
    p_import.add_argument("file")
    p_next = sub.add_parser("next-send", help="date of the next send")
    p_next.add_argument("--run-date", type=date.fromisoformat)
    args = parser.parse_args()

    # The only place that reads today's date.
    run_date: date = getattr(args, "run_date", None) or date.today()

    if args.command == "subscribers":
        subscribers = read_subscribers(args.file)
        if args.since_days is not None:
            subscribers = joined_within_days(subscribers, args.since_days, run_date)
        elif args.since is not None:
            subscribers = joined_since(subscribers, args.since, run_date)
        print(f"Total: {len(subscribers)}")
        for group, count in count_by_group(subscribers).items():
            print(f"{group}: {count}")
        consented = sum(1 for s in subscribers if s.consent != "")
        print(f"Gave consent: {consented}")
    elif args.command == "check":
        problems = check_issue(Issue.from_file(args.issue))
        if problems:
            for problem in problems:
                print(problem)
            sys.exit(1)
        print("OK")
    elif args.command == "import":
        accepted, rejected = import_rows(args.file)
        for subscriber in accepted:
            print(f"accepted: {subscriber.full_name}")
        for name, why in rejected:
            print(f"rejected: {name}: {why}")
    elif args.command == "next-send":
        print(f"Next send: {next_send_date(run_date).isoformat()}")
