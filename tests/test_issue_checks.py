from pathlib import Path
import subprocess

from mailroom.checks import check_issue
from mailroom.issue import Issue

with open("issues/issue-01.md", encoding="utf-8") as file:
    ISSUE = file.read()

FOOTER_1 = "You're getting this because you joined the Kettlebird Tea waitlist.\n"
FOOTER_2 = "Kettlebird Tea, {{company_address}} · Unsubscribe: {{unsubscribe_url}}\n"


def test_issue_01_has_no_problems() -> None:
    assert check_issue(Issue(ISSUE)) == []


def test_preview_of_91_characters_is_one_problem() -> None:
    long_preview = "x" * 91
    lines = ISSUE.splitlines(keepends=True)
    lines[1] = f"Preview: {long_preview}\n"
    problems = check_issue(Issue("".join(lines)))
    assert len(problems) == 1
    assert "Preview" in problems[0]


def test_preview_of_90_characters_is_fine() -> None:
    lines = ISSUE.splitlines(keepends=True)
    lines[1] = f"Preview: {'x' * 90}\n"
    assert check_issue(Issue("".join(lines))) == []


def test_no_first_name_is_one_problem() -> None:
    problems = check_issue(Issue(ISSUE.replace("Hi {{first_name}},", "Hi there,")))
    assert len(problems) == 1
    assert "first_name" in problems[0]


def test_two_links_one_of_them_http_is_two_problems() -> None:
    # Decided in step 24: an http:// link is a problem of its own, so this issue has two problems
    # (two links, and one of them is not https). This replaces the older "one problem" answer.
    extra = "\n[Read more](http://kettlebird.example/blog)\n"
    problems = check_issue(Issue(ISSUE.replace("Steep well,", extra + "\nSteep well,")))
    assert len(problems) == 2
    assert any("exactly one link" in p for p in problems)
    assert any("https" in p for p in problems)


def test_http_link_is_a_problem() -> None:
    text = ISSUE.replace("https://kettlebird.example/steep-club", "http://kettlebird.example/steep-club")
    problems = check_issue(Issue(text))
    assert len(problems) == 1
    assert "https" in problems[0]


def test_no_link_is_one_problem() -> None:
    problems = check_issue(Issue(ISSUE.replace("[Join The Steep Club](https://kettlebird.example/steep-club)", "Join today.")))
    assert len(problems) == 1
    assert "link" in problems[0]


def test_no_footer_and_no_greeting_is_two_problems() -> None:
    text = ISSUE.replace(FOOTER_1, "").replace(FOOTER_2, "").replace("Hi {{first_name}},", "Hello,")
    assert len(check_issue(Issue(text))) == 2


def test_missing_preview_line_is_a_problem() -> None:
    lines = ISSUE.splitlines(keepends=True)
    del lines[1]
    problems = check_issue(Issue("".join(lines)))
    assert len(problems) == 1
    assert "Preview" in problems[0]


def run_check(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["uv", "run", "mailroom", "check", path], capture_output=True, text=True)


def test_check_command_prints_ok_and_exits_0(tmp_path: Path) -> None:
    result = run_check("issues/issue-01.md")
    assert result.returncode == 0
    assert result.stdout.strip() == "OK"


def test_check_command_prints_each_problem_and_exits_1(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text(ISSUE.replace(FOOTER_1, "").replace("Hi {{first_name}},", "Hello,"), encoding="utf-8")
    result = run_check(str(bad))
    assert result.returncode == 1
    assert len(result.stdout.strip().splitlines()) == 2


def test_preview_that_repeats_the_subject_is_a_problem() -> None:
    lines = ISSUE.splitlines(keepends=True)
    lines[1] = "Preview: The Steep Club opens Monday\n"
    problems = check_issue(Issue("".join(lines)))
    assert len(problems) == 1
    assert "repeats the subject" in problems[0]


def test_preview_that_contains_the_subject_is_a_problem() -> None:
    lines = ISSUE.splitlines(keepends=True)
    lines[1] = "Preview: Big news: the steep club opens monday, with three teas.\n"
    problems = check_issue(Issue("".join(lines)))
    assert len(problems) == 1
    assert "repeats the subject" in problems[0]
