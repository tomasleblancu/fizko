"""Datetime utilities with centralized timezone configuration.

This module provides timezone-aware datetime helpers for the entire application.
All datetime operations should use these helpers to ensure consistency.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

# Application timezone (Chile)
TIMEZONE = ZoneInfo("America/Santiago")  # UTC-3 / UTC-4 (with DST)


def now() -> datetime:
    """
    Get current datetime in configured timezone.

    Returns:
        datetime: Current datetime in America/Santiago timezone

    Example:
        >>> from app.utils.datetime import now
        >>> current_time = now()
        >>> print(current_time)  # 2025-11-06 02:30:00-03:00
    """
    return datetime.now(TIMEZONE)


def utc_to_local(dt: datetime) -> datetime:
    """
    Convert UTC datetime to local timezone.

    Args:
        dt: UTC datetime (must be timezone-aware or will be assumed UTC)

    Returns:
        datetime: Datetime converted to America/Santiago timezone

    Example:
        >>> from datetime import datetime
        >>> from zoneinfo import ZoneInfo
        >>> from app.utils.datetime import utc_to_local
        >>> utc_time = datetime(2025, 11, 6, 5, 30, tzinfo=ZoneInfo("UTC"))
        >>> local_time = utc_to_local(utc_time)
        >>> print(local_time)  # 2025-11-06 02:30:00-03:00
    """
    if dt.tzinfo is None:
        # Assume UTC if no timezone
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(TIMEZONE)


def local_to_utc(dt: datetime) -> datetime:
    """
    Convert local datetime to UTC.

    Args:
        dt: Local datetime (must be timezone-aware or will be assumed local)

    Returns:
        datetime: Datetime converted to UTC timezone

    Example:
        >>> from datetime import datetime
        >>> from app.utils.datetime import local_to_utc, TIMEZONE
        >>> local_time = datetime(2025, 11, 6, 2, 30, tzinfo=TIMEZONE)
        >>> utc_time = local_to_utc(local_time)
        >>> print(utc_time)  # 2025-11-06 05:30:00+00:00
    """
    if dt.tzinfo is None:
        # Assume local timezone if no timezone
        dt = dt.replace(tzinfo=TIMEZONE)
    return dt.astimezone(ZoneInfo("UTC"))


def format_for_sqlite(dt: datetime) -> str:
    """
    Format datetime for SQLite storage.

    SQLite expects timestamps in format 'YYYY-MM-DD HH:MM:SS' without timezone.
    This function converts any datetime to local timezone and formats appropriately.

    Args:
        dt: Datetime to format (any timezone)

    Returns:
        str: Formatted datetime string for SQLite

    Example:
        >>> from datetime import datetime
        >>> from zoneinfo import ZoneInfo
        >>> from app.utils.datetime import format_for_sqlite
        >>> utc_time = datetime(2025, 11, 6, 5, 30, tzinfo=ZoneInfo("UTC"))
        >>> sqlite_str = format_for_sqlite(utc_time)
        >>> print(sqlite_str)  # '2025-11-06 02:30:00'
    """
    if dt.tzinfo is not None:
        # Convert to local timezone if timezone-aware
        dt = dt.astimezone(TIMEZONE)
    # Format without timezone info (SQLite doesn't support it)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def parse_from_sqlite(dt_str: str) -> datetime:
    """
    Parse datetime from SQLite storage.

    SQLite stores timestamps as 'YYYY-MM-DD HH:MM:SS' without timezone.
    This function parses the string and assumes it's in local timezone.

    Args:
        dt_str: SQLite datetime string

    Returns:
        datetime: Timezone-aware datetime in local timezone

    Example:
        >>> from app.utils.datetime import parse_from_sqlite
        >>> dt = parse_from_sqlite('2025-11-06 02:30:00')
        >>> print(dt)  # 2025-11-06 02:30:00-03:00
    """
    naive_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    return naive_dt.replace(tzinfo=TIMEZONE)
