"""
SQLAlchemy models for Celery Beat scheduled tasks.

These models allow storing periodic tasks in the database,
enabling dynamic creation, modification, and deletion of scheduled tasks
without restarting the Celery Beat scheduler.

IMPORTANT: These models must use celery_schema to work with sqlalchemy-celery-beat.
Table names must match what the library expects (without underscores between words).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    SmallInteger,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import Base


class IntervalSchedule(Base):
    """
    Schedule to run a task at fixed intervals.

    Examples:
        - Every 5 minutes: every=5, period='minutes'
        - Every 2 hours: every=2, period='hours'
        - Every 1 day: every=1, period='days'
    """

    __tablename__ = "celery_intervalschedule"
    __table_args__ = {'schema': 'celery_schema'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    every = Column(Integer, nullable=False, comment="Number of intervals")
    period = Column(
        String(24),
        nullable=False,
        comment="Type of interval: days, hours, minutes, seconds, microseconds",
    )

    # Relationship
    periodic_tasks = relationship(
        "PeriodicTask", back_populates="interval", cascade="all, delete-orphan"
    )

    def __str__(self):
        if self.every == 1:
            return f"every {self.period_singular}"
        return f"every {self.every} {self.period}"

    @property
    def period_singular(self):
        return self.period[:-1] if self.period.endswith("s") else self.period

    def __repr__(self):
        return f"<IntervalSchedule: {self}>"


class CrontabSchedule(Base):
    """
    Crontab-like schedule for tasks.

    Examples:
        - Every day at 2 AM: minute='0', hour='2', day_of_week='*', day_of_month='*', month_of_year='*'
        - Every Monday at 9 AM: minute='0', hour='9', day_of_week='1', day_of_month='*', month_of_year='*'
        - 1st of every month at noon: minute='0', hour='12', day_of_week='*', day_of_month='1', month_of_year='*'
    """

    __tablename__ = "celery_crontabschedule"
    __table_args__ = {'schema': 'celery_schema'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    minute = Column(String(64), nullable=False, default="*", comment="Minute (0-59, *, */N)")
    hour = Column(String(64), nullable=False, default="*", comment="Hour (0-23, *, */N)")
    day_of_week = Column(
        String(64), nullable=False, default="*", comment="Day of week (0-6, *, mon-sun)"
    )
    day_of_month = Column(
        String(64), nullable=False, default="*", comment="Day of month (1-31, *, */N)"
    )
    month_of_year = Column(
        String(64), nullable=False, default="*", comment="Month of year (1-12, *, jan-dec)"
    )
    timezone = Column(String(64), nullable=False, default="UTC", comment="Timezone name")

    # Relationship
    periodic_tasks = relationship(
        "PeriodicTask", back_populates="crontab", cascade="all, delete-orphan"
    )

    def __str__(self):
        return (
            f"{self.minute} {self.hour} {self.day_of_month} "
            f"{self.month_of_year} {self.day_of_week} (tz: {self.timezone})"
        )

    def __repr__(self):
        return f"<CrontabSchedule: {self}>"


class PeriodicTask(Base):
    """
    Periodic task definition stored in database.

    Each task can have either an interval schedule or a crontab schedule.
    """

    __tablename__ = "celery_periodictask"
    __table_args__ = {'schema': 'celery_schema'}

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Task identification
    name = Column(String(200), unique=True, nullable=False, comment="Unique task name")
    task = Column(String(200), nullable=False, comment="Celery task name (e.g., 'sii.sync_documents')")

    # Schedule (one of interval or crontab must be set)
    interval_id = Column(Integer, ForeignKey("celery_schema.celery_intervalschedule.id"), nullable=True)
    crontab_id = Column(Integer, ForeignKey("celery_schema.celery_crontabschedule.id"), nullable=True)

    # Task arguments (stored as JSON strings, not JSONB objects)
    # sqlalchemy-celery-beat expects TEXT with JSON strings
    args = Column(Text, nullable=False, default='[]', comment="Positional arguments as JSON string")
    kwargs = Column(Text, nullable=False, default='{}', comment="Keyword arguments as JSON string")

    # Task options
    queue = Column(
        String(200),
        nullable=True,
        comment="Queue to send task to (high, default, low, or custom)",
    )
    exchange = Column(String(200), nullable=True, comment="Exchange to use")
    routing_key = Column(String(200), nullable=True, comment="Routing key")
    headers = Column(Text, nullable=False, default='{}', comment="JSON encoded message headers")
    priority = Column(SmallInteger, nullable=True, comment="Task priority (0-255)")

    # Expiration and limits
    expires = Column(DateTime, nullable=True, comment="Task expiration datetime")
    expire_seconds = Column(Integer, nullable=True, comment="Task expiration in seconds")
    one_off = Column(Boolean, nullable=False, default=False, comment="Run only once then delete")
    start_time = Column(DateTime, nullable=True, comment="Datetime when schedule should begin triggering")
    max_retries = Column(Integer, nullable=True, comment="Maximum retry attempts")
    soft_time_limit = Column(Integer, nullable=True, comment="Soft time limit in seconds")
    hard_time_limit = Column(Integer, nullable=True, comment="Hard time limit in seconds")

    # Execution control
    enabled = Column(Boolean, nullable=False, default=True, comment="Whether task is enabled")
    last_run_at = Column(DateTime, nullable=True, comment="Last time task was run")
    total_run_count = Column(Integer, nullable=False, default=0, comment="Total number of runs")

    # Required by sqlalchemy-celery-beat for generic foreign key pattern
    discriminator = Column(String(20), nullable=False, comment="Lower case name of schedule class")
    schedule_id = Column(Integer, nullable=False, comment="ID of the schedule model object")

    # Metadata
    date_changed = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = Column(Text, nullable=True, comment="Human-readable description")

    # Multi-tenancy
    company_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=True,
        comment="Company that owns this scheduled task (NULL for system-level tasks)"
    )

    # Relationships
    interval = relationship("IntervalSchedule", back_populates="periodic_tasks")
    crontab = relationship("CrontabSchedule", back_populates="periodic_tasks")

    def __str__(self):
        fmt = "{0.name}: {{no schedule}}"
        if self.interval:
            fmt = "{0.name}: {0.interval}"
        elif self.crontab:
            fmt = "{0.name}: {0.crontab}"
        return fmt.format(self)

    def __repr__(self):
        return f"<PeriodicTask: {self.name} ({self.task})>"


class PeriodicTaskChanged(Base):
    """
    Track changes to periodic tasks to notify scheduler.

    This table is used by Celery Beat to detect when tasks have been
    modified and needs to reload the schedule.
    """

    __tablename__ = "celery_periodictaskchanged"
    __table_args__ = {'schema': 'celery_schema'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_update = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Timestamp of last change",
    )

    def __repr__(self):
        return f"<PeriodicTaskChanged: {self.last_update}>"


class TaskResult(Base):
    """
    Store results of task executions (optional).

    Enable this if you want to track execution history and results.
    """

    __tablename__ = "celery_taskresult"
    __table_args__ = {'schema': 'celery_schema'}

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Task identification
    task_id = Column(String(255), unique=True, nullable=False, comment="Celery task ID (UUID)")
    task_name = Column(String(255), nullable=True, comment="Task name")
    periodic_task_name = Column(
        String(255), nullable=True, comment="Name of periodic task that spawned this"
    )

    # Execution info
    status = Column(
        String(50), nullable=False, comment="PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED"
    )
    worker = Column(String(100), nullable=True, comment="Worker hostname")
    content_type = Column(String(128), nullable=False, default="application/json")
    content_encoding = Column(String(64), nullable=False, default="utf-8")

    # Result data
    result = Column(JSONB, nullable=True, comment="Task result as JSON")
    traceback = Column(Text, nullable=True, comment="Exception traceback if failed")

    # Timing
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_done = Column(DateTime, nullable=True, comment="When task completed")
    runtime = Column(Float, nullable=True, comment="Execution time in seconds")

    # Multi-tenancy
    company_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=True,
        comment="Company that owns this task result (NULL for system-level tasks)"
    )

    def __repr__(self):
        return f"<TaskResult: {self.task_id} ({self.status})>"


# Helper functions for creating schedules

def create_interval_schedule(every: int, period: str) -> dict:
    """
    Helper to create interval schedule data.

    Args:
        every: Number of intervals
        period: Type of interval (days, hours, minutes, seconds)

    Returns:
        Dict with schedule data

    Example:
        >>> create_interval_schedule(5, "minutes")
        {'every': 5, 'period': 'minutes'}
    """
    valid_periods = ["days", "hours", "minutes", "seconds", "microseconds"]
    if period not in valid_periods:
        raise ValueError(f"period must be one of: {valid_periods}")

    return {"every": every, "period": period}


def create_crontab_schedule(
    minute: str = "*",
    hour: str = "*",
    day_of_week: str = "*",
    day_of_month: str = "*",
    month_of_year: str = "*",
    timezone: str = "America/Santiago",
) -> dict:
    """
    Helper to create crontab schedule data.

    Args:
        minute: Minute (0-59, *, */N)
        hour: Hour (0-23, *, */N)
        day_of_week: Day of week (0-6, mon-sun, *)
        day_of_month: Day of month (1-31, *, */N)
        month_of_year: Month (1-12, jan-dec, *, */N)
        timezone: Timezone name (default: America/Santiago)

    Returns:
        Dict with schedule data

    Examples:
        >>> create_crontab_schedule(minute="0", hour="2")  # Every day at 2 AM
        >>> create_crontab_schedule(minute="0", hour="9", day_of_week="1")  # Every Monday at 9 AM
        >>> create_crontab_schedule(minute="0", hour="12", day_of_month="1")  # 1st of month at noon
    """
    return {
        "minute": minute,
        "hour": hour,
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "month_of_year": month_of_year,
        "timezone": timezone,
    }
