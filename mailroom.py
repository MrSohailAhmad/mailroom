import csv
import sys


def read_subscribers(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def count_by_group(subscribers):
    counts = {}
    for subscriber in subscribers:
        group = subscriber["group"]
        counts[group] = counts.get(group, 0) + 1
    return counts


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "subscribers":
        path = sys.argv[2] if len(sys.argv) > 2 else "data/subscribers.csv"
        subscribers = read_subscribers(path)
        print(f"Total: {len(subscribers)}")
        for group, count in count_by_group(subscribers).items():
            print(f"{group}: {count}")
        consented = sum(1 for s in subscribers if s["consent"] != "")
        print(f"Gave consent: {consented}")
    else:
        print("Usage: mailroom.py subscribers [file]")


if __name__ == "__main__":
    main()
