"""Date/time utilities for booking windows and timezone handling."""
from datetime import datetime, timedelta

import pytz
import tzlocal


def get_local_timezone() -> str:
    """Get system's local timezone name."""
    return tzlocal.get_localzone_name()


def set_start_of_day(dt: datetime) -> datetime:
    """Set the start of the day for the provided date."""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def set_end_of_day(dt: datetime) -> datetime:
    """Set the end of the day for the provided date."""
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def parse_datetime(hour: str, baseline: datetime) -> datetime:
    """Parse a time string (HH:MM or HH:MM:SS) into a datetime using baseline date."""
    time_parts = hour.strip().split(":")
    if len(time_parts) < 2:
        raise ValueError("Time must be in HH:MM or HH:MM:SS format.")
    h, m = int(time_parts[0]), int(time_parts[1])
    sec = int(time_parts[2]) if len(time_parts) > 2 else 0
    return baseline.replace(hour=h, minute=m, second=sec, microsecond=0)


def parse_utc_to_local(utc_date: datetime) -> datetime:
    """Convert UTC datetime to local timezone."""
    utc_date = utc_date.replace(tzinfo=pytz.UTC)
    local_tz = get_local_timezone()
    return utc_date.astimezone(pytz.timezone(local_tz))


def is_within_current_week(dt: datetime) -> bool:
    """Check if the given date is within the current week (Mon–Sun)."""
    current = set_start_of_day(dt)
    start_of_week = current - timedelta(days=current.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week <= dt <= end_of_week
