from mailroom.issue import Issue

MAX_SUBJECT = 50
MAX_PREVIEW = 90


def check_subject(issue: Issue) -> list[str]:
    if issue.subject is None:
        return ["Subject line is missing"]
    if issue.subject == "":
        return ["Subject is empty"]
    if len(issue.subject) > MAX_SUBJECT:
        return [f"Subject is too long: {len(issue.subject)} characters (max {MAX_SUBJECT})"]
    return []


def check_preview(issue: Issue) -> list[str]:
    if issue.preview is None:
        return ["Preview line is missing"]
    if issue.preview == "":
        return ["Preview is empty"]
    if len(issue.preview) > MAX_PREVIEW:
        return [f"Preview is too long: {len(issue.preview)} characters (max {MAX_PREVIEW})"]
    return []


def check_greeting(issue: Issue) -> list[str]:
    if "{{first_name}}" not in issue.body:
        return ["No greeting with {{first_name}}"]
    return []


def check_links(issue: Issue) -> list[str]:
    count = len(issue.links)
    if count != 1:
        return [f"Expected exactly one link, found {count}"]
    return []


def check_footer(issue: Issue) -> list[str]:
    lines = issue.text.splitlines()
    has_reason = any(line.startswith("You're getting this because") for line in lines)
    has_unsubscribe = any("Unsubscribe: {{unsubscribe_url}}" in line for line in lines)
    if not (has_reason and has_unsubscribe):
        return ["Footer is missing or incomplete"]
    return []


def check_issue(issue: Issue) -> list[str]:
    problems: list[str] = []
    problems += check_subject(issue)
    problems += check_preview(issue)
    problems += check_greeting(issue)
    problems += check_links(issue)
    problems += check_footer(issue)
    return problems
