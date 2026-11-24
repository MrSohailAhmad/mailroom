import re

LINK = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")


def read_issue(path):
    with open(path, encoding="utf-8") as file:
        return file.read()


def find_line(issue_text, prefix):
    for line in issue_text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):]
    return None


def find_links(issue_text):
    return LINK.findall(issue_text)
