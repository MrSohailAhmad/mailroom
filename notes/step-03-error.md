# Step 3: the 30th of February

Changed Jonas Berg's joined_on to 2026-02-30 and ran
`uv run mailroom.py subscribers --since-days 30 --run-date 2026-11-20`.

Read bottom up:
- Last line: `ValueError: day is out of range for month` (type ValueError).
- Lowest line in our code: mailroom.py, function `joined_on`, `date.fromisoformat(subscriber["joined_on"])`.
- The error does not say which row it was.

In three lines: Python could not turn "2026-02-30" into a date, because February has no 30th.
It happened in `joined_on`, called from `joined_since` while counting the last 30 days.
The code is fine; the data was wrong, so the data was restored from git (2026-10-15).
