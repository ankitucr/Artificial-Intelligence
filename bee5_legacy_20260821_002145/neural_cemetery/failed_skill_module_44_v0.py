# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

from datetime import date, timedelta
from typing import List

def is_leap_year(year: int) -> bool:
    """Check if a year is a leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def get_days_in_month(year: int, month: int) -> int:
    """Get the number of days in a month."""
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month == 2:
        return 29 if is_leap_year(year) else 28
    else:
        return 30

def add_days(date_obj: date, days: int) -> date:
    """Add a specified number of days to a date."""
    return date_obj + timedelta(days=days)

def subtract_days(date_obj: date, days: int) -> date:
    """Subtract a specified number of days from a date."""
    return date_obj - timedelta(days=days)

def get_date_range(start_date: date, end_date: date) -> List[date]:
    """Get a list of dates between two dates (inclusive)."""
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date = add_days(current_date, 1)
    return dates

if __name__ == "__main__":
    start_date = date(2022, 1, 1)
    end_date = date(2022, 1, 10)
    date_range = get_date_range(start_date, end_date)
    expected_dates = [
        date(2022, 1, 1), date(2022, 1, 2), date(2022, 1, 3), date(2022, 1, 4),
        date(2022, 1, 5), date(2022, 1, 6), date(2022, 1, 7), date(2022, 1, 8),
        date(2022, 1, 9), date(2022, 1, 10)
    ]
    assert date_range == expected_dates, "Date range is incorrect"