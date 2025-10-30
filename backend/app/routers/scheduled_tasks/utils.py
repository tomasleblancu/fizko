"""Utility functions for scheduled tasks."""

import json
from app.db.models.scheduled_tasks import PeriodicTask
from app.routers.scheduled_tasks.schemas import ScheduledTaskResponse


def format_task_response(task: PeriodicTask) -> ScheduledTaskResponse:
    """
    Format PeriodicTask model into response format.

    Args:
        task: The PeriodicTask SQLAlchemy model instance.

    Returns:
        ScheduledTaskResponse: Formatted response with schedule display string.
    """
    # Determine schedule type and display string
    if task.interval:
        schedule_type = "interval"
        schedule_display = f"Every {task.interval.every} {task.interval.period}"
    elif task.crontab:
        schedule_type = "crontab"
        c = task.crontab
        schedule_display = (
            f"Cron: {c.minute} {c.hour} {c.day_of_month} {c.month_of_year} {c.day_of_week}"
        )
        if c.timezone != "UTC":
            schedule_display += f" ({c.timezone})"
    else:
        schedule_type = "unknown"
        schedule_display = "No schedule"

    # Parse args and kwargs from JSON strings to objects
    # sqlalchemy-celery-beat stores them as TEXT (JSON strings), not JSONB
    try:
        args = json.loads(task.args) if isinstance(task.args, str) else task.args
    except (json.JSONDecodeError, TypeError):
        args = []

    try:
        kwargs = json.loads(task.kwargs) if isinstance(task.kwargs, str) else task.kwargs
    except (json.JSONDecodeError, TypeError):
        kwargs = {}

    return ScheduledTaskResponse(
        id=task.id,
        name=task.name,
        task=task.task,
        schedule_type=schedule_type,
        schedule_display=schedule_display,
        args=args,
        kwargs=kwargs,
        queue=task.queue,
        priority=task.priority,
        enabled=task.enabled,
        one_off=task.one_off,
        expires=task.expires,
        max_retries=task.max_retries,
        soft_time_limit=task.soft_time_limit,
        hard_time_limit=task.hard_time_limit,
        description=task.description,
        date_changed=task.date_changed,
        last_run_at=task.last_run_at,
        total_run_count=task.total_run_count,
    )
