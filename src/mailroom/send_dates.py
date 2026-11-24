from datetime import date, timedelta


def first_monday(year, month):
    day = date(year, month, 1)
    while day.weekday() != 0:
        day += timedelta(days=1)
    return day


def next_send_date(run_date):
    if run_date.month == 12:
        return first_monday(run_date.year + 1, 1)
    return first_monday(run_date.year, run_date.month + 1)
