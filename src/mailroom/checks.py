from mailroom.issue import find_line, find_links

MAX_SUBJECT = 50


def check_subject(issue_text: str) -> list[str]:
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


def check_preview(issue_text: str) -> list[str]:
    preview = find_line(issue_text, "Preview:")
    if preview is None:
        return ["Preview line is missing"]
    preview = preview.strip()
    if preview == "":
        return ["Preview is empty"]
    if len(preview) > MAX_PREVIEW:
        return [f"Preview is too long: {len(preview)} characters (max {MAX_PREVIEW})"]
    return []


def check_greeting(issue_text: str) -> list[str]:
    if "{{first_name}}" not in issue_text:
        return ["No greeting with {{first_name}}"]
    return []


def check_links(issue_text: str) -> list[str]:
    count = len(find_links(issue_text))
    if count != 1:
        return [f"Expected exactly one link, found {count}"]
    return []


def check_footer(issue_text: str) -> list[str]:
    lines = issue_text.splitlines()
    has_reason = any(line.startswith("You're getting this because") for line in lines)
    has_unsubscribe = any("Unsubscribe: {{unsubscribe_url}}" in line for line in lines)
    if not (has_reason and has_unsubscribe):
        return ["Footer is missing or incomplete"]
    return []


def check_issue(issue_text: str) -> list[str]:
    problems: list[str] = []
    problems += check_subject(issue_text)
    problems += check_preview(issue_text)
    problems += check_greeting(issue_text)
    problems += check_links(issue_text)
    problems += check_footer(issue_text)
    return problems
