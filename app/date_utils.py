"""
Utility functions for working with timestamps in milliseconds.
These functions provide current and future datetime calculations
formatted as Unix timestamps in milliseconds.
"""
from datetime import datetime, timedelta


def current_timestamp_millis() -> int:
    """
    Returns:
        current unix timestamp in milliseconds
    """
    return int(datetime.now().timestamp() * 1000)


def next_day_timestamp_millis() -> int:
    """
    Returns:
        unix timestamp of the next day at the same time in milliseconds
    """
    next_day = datetime.now() + timedelta(days=1)
    return int(next_day.timestamp() * 1000)
