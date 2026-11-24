from mailroom import count_by_group, read_subscribers

subscribers = read_subscribers("data/subscribers.csv")
assert len(subscribers) == 24
groups = count_by_group(subscribers)
assert groups["tea-curious"] == 8
assert groups["gift-buyers"] == 8
assert groups["daily-drinkers"] == 8
assert sum(1 for s in subscribers if s["consent"] != "") == 24

from datetime import date
from mailroom import joined_since, joined_within_days, next_send_date

assert len(joined_within_days(subscribers, 30, date(2026, 11, 20))) == 7
assert any(s["first_name"] == "Amara" for s in joined_within_days(subscribers, 30, date(2026, 11, 20)))
assert next_send_date(date(2026, 11, 20)) == date(2026, 12, 7)
assert next_send_date(date(2026, 12, 7)) == date(2027, 1, 4)
assert next_send_date(date(2026, 12, 31)) == date(2027, 1, 4)
assert len(joined_since(subscribers, date(2026, 10, 1), date(2026, 11, 20))) == 12
print("Date checks passed")
