"""Date and time utility functions."""
from datetime import date, datetime, timedelta, time
from typing import List


DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def most_recent_sunday(d: date) -> date:
    """Get the most recent Sunday from given date (inclusive)."""
    days_since_sun = (d.weekday() + 1) % 7
    return d - timedelta(days=days_since_sun)


def parse_start_sunday(s: str) -> date:
    """Parse start date string or auto-detect most recent Sunday."""
    if s.strip() == "":
        return most_recent_sunday(date.today())
    return date.fromisoformat(s)


def week_start_for(start_sunday: date, week_index: int) -> date:
    """Get the start date for a given week index."""
    return start_sunday + timedelta(days=7 * week_index)


def dt_on(week_start: date, dow_index: int, due_t: time) -> datetime:
    """Create datetime for specific day of week with given time."""
    return datetime.combine(week_start + timedelta(days=dow_index), due_t)


def unique_sorted_days(days: List[int]) -> List[int]:
    """Remove duplicates and sort day indices."""
    return sorted(set(days))


def week_index_from_anchor(anchor_sunday: date, current_sunday: date) -> int:
    """Calculate week index from anchor Sunday (for biweekly parity)."""
    return (current_sunday - anchor_sunday).days // 7
