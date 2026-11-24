from mailroom import check_subject

BODY = "\nPreview: A short preview\n\nHi {{first_name}},\n"


def issue_with_subject(subject):
    return f"Subject: {subject}{BODY}"


def test_normal_subject_has_no_problems():
    assert check_subject(issue_with_subject("The Steep Club opens Monday")) == []


def test_subject_of_exactly_50_characters_is_fine():
    assert check_subject(issue_with_subject("Your Steep Club box ships on Monday with new teas.")) == []


def test_subject_of_51_characters_is_too_long():
    problems = check_subject(issue_with_subject("Your Steep Club box ships on Monday with fresh teas"))
    assert len(problems) == 1
    assert "too long" in problems[0]


def test_empty_subject_is_a_problem():
    problems = check_subject(issue_with_subject(""))
    assert len(problems) == 1
    assert "empty" in problems[0]


def test_subject_of_only_spaces_is_empty():
    problems = check_subject(issue_with_subject("    "))
    assert len(problems) == 1
    assert "empty" in problems[0]


def test_missing_subject_line_is_a_problem():
    problems = check_subject("Preview: A short preview\n\nHi {{first_name}},\n")
    assert len(problems) == 1
    assert "missing" in problems[0]
