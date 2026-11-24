from mailroom import count_by_group, read_subscribers

subscribers = read_subscribers("data/subscribers.csv")
assert len(subscribers) == 24
groups = count_by_group(subscribers)
assert groups["tea-curious"] == 8
assert groups["gift-buyers"] == 8
assert groups["daily-drinkers"] == 8
assert sum(1 for s in subscribers if s["consent"] != "") == 24
print("All checks passed")
