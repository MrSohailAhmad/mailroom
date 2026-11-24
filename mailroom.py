import argparse
import csv
import re
import sys
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


def first_monday(year, month):
    day = date(year, month, 1)
    while day.weekday() != 0:
        day += timedelta(days=1)
    return day


def next_send_date(run_date):
    if run_date.month == 12:
        return first_monday(run_date.year + 1, 1)
    return first_monday(run_date.year, run_date.month + 1)


MAX_SUBJECT = 50


def find_line(issue_text, prefix):
    for line in issue_text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):]
    return None


def check_subject(issue_text):
    subject = find_line(issue_text, "Subject:")
    if subject is None:
        return ["Subject line is missing"]
    subject = subject.strip()
    if subject == "":
        return ["Subject is empty"]
    if len(subject) > MAX_SUBJECT:
        return [f"Subject is too long: {len(subject)} characters (max {MAX_SUBJECT})"]
    return []


MAX_PREVIEW = 90
LINK = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")


def check_preview(issue_text):
    preview = find_line(issue_text, "Preview:")
    if preview is None:
        return ["Preview line is missing"]
    preview = preview.strip()
    if preview == "":
        return ["Preview is empty"]
    if len(preview) > MAX_PREVIEW:
        return [f"Preview is too long: {len(preview)} characters (max {MAX_PREVIEW})"]
    return []


def check_greeting(issue_text):
    if "{{first_name}}" not in issue_text:
        return ["No greeting with {{first_name}}"]
    return []


def find_links(issue_text):
    return LINK.findall(issue_text)


def check_links(issue_text):
    count = len(find_links(issue_text))
    if count != 1:
        return [f"Expected exactly one link, found {count}"]
    return []


def check_footer(issue_text):
    lines = issue_text.splitlines()
    has_reason = any(line.startswith("You're getting this because") for line in lines)
    has_unsubscribe = any("Unsubscribe: {{unsubscribe_url}}" in line for line in lines)
    if not (has_reason and has_unsubscribe):
        return ["Footer is missing or incomplete"]
    return []


def check_issue(issue_text):
    problems = []
    problems += check_subject(issue_text)
    problems += check_preview(issue_text)
    problems += check_greeting(issue_text)
    problems += check_links(issue_text)
    problems += check_footer(issue_text)
    return problems


def main():
    parser = argparse.ArgumentParser(prog="mailroom")
    sub = parser.add_subparsers(dest="command", required=True)
    p_subs = sub.add_parser("subscribers", help="count subscribers")
    p_subs.add_argument("file", nargs="?", default="data/subscribers.csv")
    p_subs.add_argument("--since-days", type=int)
    p_subs.add_argument("--since", type=date.fromisoformat)
    p_subs.add_argument("--run-date", type=date.fromisoformat)
    p_check = sub.add_parser("check", help="check an issue against the rules")
    p_check.add_argument("issue")
    p_next = sub.add_parser("next-send", help="date of the next send")
    p_next.add_argument("--run-date", type=date.fromisoformat)
    args = parser.parse_args()

    # The only place that reads today's date.
    run_date = args.run_date or date.today()

    if args.command == "subscribers":
        subscribers = read_subscribers(args.file)
        if args.since_days is not None:
            subscribers = joined_within_days(subscribers, args.since_days, run_date)
        elif args.since is not None:
            subscribers = joined_since(subscribers, args.since, run_date)
        print(f"Total: {len(subscribers)}")
        for group, count in count_by_group(subscribers).items():
            print(f"{group}: {count}")
        consented = sum(1 for s in subscribers if s["consent"] != "")
        print(f"Gave consent: {consented}")
    elif args.command == "check":
        with open(args.issue, encoding="utf-8") as file:
            problems = check_issue(file.read())
        if problems:
            for problem in problems:
                print(problem)
            sys.exit(1)
        print("OK")
    elif args.command == "next-send":
        print(f"Next send: {next_send_date(run_date).isoformat()}")


if __name__ == "__main__":
    main()
