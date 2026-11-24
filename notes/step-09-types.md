# Step 9: a date that was really text

Calling `joined_within_days(SUBSCRIBERS, 30, "2026-11-20")` crashed at run time:
`TypeError: unsupported operand type(s) for -: 'str' and 'datetime.timedelta'` in `subscribers.py`.

After type hints, pyright (strict) flagged it before running:
`Argument of type "Literal['2026-11-20']" cannot be assigned to parameter "run_date" of type "date"`.

Fixed the call (pass a real date), not the hint.
