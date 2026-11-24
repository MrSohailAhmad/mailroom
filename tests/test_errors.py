import subprocess
from datetime import date
from pathlib import Path

import pytest

from mailroom.subscribers import DataFileError, load_subscribers


def test_new_signups_give_2_good_and_6_problems() -> None:
    result = load_subscribers("data/new-signups.csv", date(2026, 11, 20))
    assert [s.first_name for s in result.good] == ["Maria", "Ines"]
    assert len(result.problems) == 6


def test_every_problem_names_its_row_and_field() -> None:
    result = load_subscribers("data/new-signups.csv", date(2026, 11, 20))
    rows = {(p.row, p.field) for p in result.problems}
    assert (3, "email") in rows  # Omar, no email
    assert (4, "consent") in rows  # Lena
    assert (5, "group") in rows  # Kofi
    assert (6, "joined_on") in rows  # Hana
    assert (7, "email") in rows  # Sara, gmail
    assert (8, "joined_on") in rows  # Tom, after the run date


def test_missing_file_is_a_data_file_error() -> None:
    with pytest.raises(DataFileError):
        load_subscribers("data/nope.csv", date(2026, 11, 20))


def test_wrong_columns_is_a_data_file_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("first_name,last_name,email,group,joined,consent\n", encoding="utf-8")
    with pytest.raises(DataFileError):
        load_subscribers(str(bad), date(2026, 11, 20))


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["uv", "run", "mailroom", *args], capture_output=True, text=True)


def test_import_prints_all_problems_and_exits_1() -> None:
    result = run("import", "data/new-signups.csv", "--run-date", "2026-11-20")
    assert result.returncode == 1
    assert result.stdout.count("row ") == 6


def test_missing_file_exits_2_with_one_sentence_and_no_traceback() -> None:
    result = run("import", "data/nope.csv", "--run-date", "2026-11-20")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert len(result.stderr.strip().splitlines()) == 1
