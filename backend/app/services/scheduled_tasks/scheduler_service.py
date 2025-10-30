"""
Service for managing scheduled tasks (Celery Beat periodic tasks).

This service encapsulates all business logic for creating, updating, and managing
periodic tasks stored in the database. It separates concerns from HTTP routing.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.scheduled_tasks import (
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    TaskResult,
)
from app.routers.scheduled_tasks.schemas import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
)

from .beat_service import BeatService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled tasks."""

    def __init__(self, db: AsyncSession):
        """
        Initialize SchedulerService.

        Args:
            db: Database session for operations
        """
        self.db = db
        self.beat_service = BeatService(db)

    async def create_scheduled_task(
        self, request: ScheduledTaskCreate, company_id: Optional[UUID] = None
    ) -> PeriodicTask:
        """
        Create a new scheduled task.

        Args:
            request: Task creation request with schedule and parameters
            company_id: Optional company ID for multi-tenancy (None for system tasks)

        Returns:
            Created PeriodicTask instance

        Raises:
            ValueError: If task name already exists or schedule is invalid
        """
        # Check if task name already exists
        existing = await self.db.execute(
            select(PeriodicTask)
            .where(PeriodicTask.name == request.name)
            .where(PeriodicTask.company_id == company_id)
        )
        if existing.scalar_one_or_none():
            scope = "company" if company_id else "system"
            raise ValueError(f"Task with name '{request.name}' already exists ({scope} level)")

        # Create or get schedule
        if request.schedule_type == "interval":
            schedule = await self._get_or_create_interval_schedule(
                every=request.interval_every, period=request.interval_period
            )
            interval_id = schedule.id
            crontab_id = None
            discriminator = "intervalschedule"
            schedule_id = interval_id
        else:  # crontab
            schedule = await self._get_or_create_crontab_schedule(
                minute=request.crontab_minute or "*",
                hour=request.crontab_hour or "*",
                day_of_week=request.crontab_day_of_week or "*",
                day_of_month=request.crontab_day_of_month or "*",
                month_of_year=request.crontab_month_of_year or "*",
                timezone=request.crontab_timezone or "America/Santiago",
            )
            interval_id = None
            crontab_id = schedule.id
            discriminator = "crontabschedule"
            schedule_id = crontab_id

        # Convert args and kwargs to JSON strings
        args_json = json.dumps(request.args) if request.args else "[]"
        kwargs_json = json.dumps(request.kwargs) if request.kwargs else "{}"

        # Create periodic task
        periodic_task = PeriodicTask(
            name=request.name,
            task=request.task,
            interval_id=interval_id,
            crontab_id=crontab_id,
            discriminator=discriminator,
            schedule_id=schedule_id,
            args=args_json,
            kwargs=kwargs_json,
            queue=request.queue,
            priority=request.priority,
            enabled=request.enabled,
            one_off=request.one_off,
            expires=request.expires,
            max_retries=request.max_retries,
            soft_time_limit=request.soft_time_limit,
            hard_time_limit=request.hard_time_limit,
            description=request.description,
            company_id=company_id,
        )

        # Set initial last_run_at based on run_now flag
        if request.run_now:
            # Execute immediately: set last_run_at in the past
            if interval_id:
                # For interval: make it overdue
                periodic_task.last_run_at = datetime.utcnow() - timedelta(
                    **{schedule.period: schedule.every}
                )
            else:
                # For crontab: set to 1 minute ago
                periodic_task.last_run_at = datetime.utcnow() - timedelta(minutes=1)
        else:
            # Schedule for future
            periodic_task.last_run_at = datetime.utcnow()

        self.db.add(periodic_task)

        # Notify Beat that schedule has changed
        await self.beat_service.notify_schedule_changed()

        await self.db.commit()
        await self.db.refresh(periodic_task)

        # Load schedule relationships
        await self.db.refresh(periodic_task, ["interval", "crontab"])

        logger.info(
            f"Created scheduled task '{request.name}' (task={request.task}, "
            f"company_id={company_id}, enabled={request.enabled})"
        )

        return periodic_task

    async def list_scheduled_tasks(
        self, enabled: Optional[bool] = None, company_id: Optional[UUID] = None
    ) -> List[PeriodicTask]:
        """
        List scheduled tasks, optionally filtered by enabled status and company.

        Args:
            enabled: Optional filter by enabled status
            company_id: Optional company ID filter (None for system tasks)

        Returns:
            List of PeriodicTask instances with loaded relationships
        """
        query = (
            select(PeriodicTask)
            .options(joinedload(PeriodicTask.interval), joinedload(PeriodicTask.crontab))
            .where(PeriodicTask.company_id == company_id)
        )

        if enabled is not None:
            query = query.where(PeriodicTask.enabled == enabled)

        result = await self.db.execute(query.order_by(PeriodicTask.name))
        tasks = result.scalars().all()

        logger.debug(f"Listed {len(tasks)} scheduled tasks (company_id={company_id})")
        return list(tasks)

    async def get_scheduled_task(
        self, task_id: int, company_id: Optional[UUID] = None
    ) -> Optional[PeriodicTask]:
        """
        Get a specific scheduled task by ID.

        Args:
            task_id: Task ID
            company_id: Optional company ID for RLS check (None for system tasks)

        Returns:
            PeriodicTask instance or None if not found
        """
        result = await self.db.execute(
            select(PeriodicTask)
            .options(joinedload(PeriodicTask.interval), joinedload(PeriodicTask.crontab))
            .where(PeriodicTask.id == task_id)
            .where(PeriodicTask.company_id == company_id)
        )
        task = result.scalar_one_or_none()

        if task:
            logger.debug(f"Retrieved task {task_id} (name='{task.name}')")
        else:
            logger.debug(f"Task {task_id} not found or access denied")

        return task

    async def update_scheduled_task(
        self, task_id: int, request: ScheduledTaskUpdate, company_id: Optional[UUID] = None
    ) -> Optional[PeriodicTask]:
        """
        Update an existing scheduled task.

        Note: Cannot change schedule type or parameters. Delete and recreate for that.

        Args:
            task_id: Task ID to update
            request: Update request with new values
            company_id: Optional company ID for RLS check

        Returns:
            Updated PeriodicTask instance or None if not found
        """
        # Get existing task
        task = await self.get_scheduled_task(task_id, company_id)
        if not task:
            return None

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        if update_data:
            await self.db.execute(
                update(PeriodicTask)
                .where(PeriodicTask.id == task_id)
                .where(PeriodicTask.company_id == company_id)
                .values(**update_data)
            )

            # Notify Beat that schedule has changed
            await self.beat_service.notify_schedule_changed()

            await self.db.commit()

        # Refresh and return
        await self.db.refresh(task)
        await self.db.refresh(task, ["interval", "crontab"])

        logger.info(f"Updated scheduled task {task_id} (name='{task.name}')")
        return task

    async def delete_scheduled_task(
        self, task_id: int, company_id: Optional[UUID] = None
    ) -> bool:
        """
        Delete a scheduled task.

        Args:
            task_id: Task ID to delete
            company_id: Optional company ID for RLS check

        Returns:
            True if deleted, False if not found
        """
        # Check if task exists
        task = await self.get_scheduled_task(task_id, company_id)
        if not task:
            return False

        task_name = task.name

        # Delete task
        await self.db.execute(
            delete(PeriodicTask)
            .where(PeriodicTask.id == task_id)
            .where(PeriodicTask.company_id == company_id)
        )

        # Notify Beat that schedule has changed
        await self.beat_service.notify_schedule_changed()

        await self.db.commit()

        logger.info(f"Deleted scheduled task {task_id} (name='{task_name}')")
        return True

    async def set_task_enabled(
        self, task_id: int, enabled: bool, company_id: Optional[UUID] = None
    ) -> Optional[PeriodicTask]:
        """
        Enable or disable a scheduled task.

        Args:
            task_id: Task ID
            enabled: True to enable, False to disable
            company_id: Optional company ID for RLS check

        Returns:
            Updated PeriodicTask or None if not found
        """
        await self.db.execute(
            update(PeriodicTask)
            .where(PeriodicTask.id == task_id)
            .where(PeriodicTask.company_id == company_id)
            .values(enabled=enabled)
        )

        # Notify Beat that schedule has changed
        await self.beat_service.notify_schedule_changed()

        await self.db.commit()

        task = await self.get_scheduled_task(task_id, company_id)
        if task:
            action = "enabled" if enabled else "disabled"
            logger.info(f"Task {task_id} (name='{task.name}') {action}")

        return task

    async def get_task_executions(
        self, task_id: int, limit: int = 20, company_id: Optional[UUID] = None
    ) -> List[TaskResult]:
        """
        Get execution history for a scheduled task.

        Args:
            task_id: Task ID
            limit: Maximum number of executions to return (capped at 100)
            company_id: Optional company ID for RLS check

        Returns:
            List of TaskResult instances
        """
        # Get task to verify it exists
        task = await self.get_scheduled_task(task_id, company_id)
        if not task:
            return []

        # Get execution history
        limit = min(limit, 100)  # Cap at 100
        result = await self.db.execute(
            select(TaskResult)
            .where(TaskResult.task_name == task.task)
            .where(TaskResult.company_id == company_id)
            .order_by(desc(TaskResult.date_created))
            .limit(limit)
        )
        executions = result.scalars().all()

        logger.debug(f"Retrieved {len(executions)} executions for task {task_id}")
        return list(executions)

    # Private helper methods

    async def _get_or_create_interval_schedule(
        self, every: int, period: str
    ) -> IntervalSchedule:
        """Get existing interval schedule or create new one."""
        result = await self.db.execute(
            select(IntervalSchedule)
            .where(IntervalSchedule.every == every)
            .where(IntervalSchedule.period == period)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            schedule = IntervalSchedule(every=every, period=period)
            self.db.add(schedule)
            await self.db.flush()  # Get the ID without committing
            logger.debug(f"Created new interval schedule: every {every} {period}")

        return schedule

    async def _get_or_create_crontab_schedule(
        self,
        minute: str,
        hour: str,
        day_of_week: str,
        day_of_month: str,
        month_of_year: str,
        timezone: str,
    ) -> CrontabSchedule:
        """Get existing crontab schedule or create new one."""
        result = await self.db.execute(
            select(CrontabSchedule)
            .where(CrontabSchedule.minute == minute)
            .where(CrontabSchedule.hour == hour)
            .where(CrontabSchedule.day_of_week == day_of_week)
            .where(CrontabSchedule.day_of_month == day_of_month)
            .where(CrontabSchedule.month_of_year == month_of_year)
            .where(CrontabSchedule.timezone == timezone)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            schedule = CrontabSchedule(
                minute=minute,
                hour=hour,
                day_of_week=day_of_week,
                day_of_month=day_of_month,
                month_of_year=month_of_year,
                timezone=timezone,
            )
            self.db.add(schedule)
            await self.db.flush()  # Get the ID without committing
            logger.debug(
                f"Created new crontab schedule: {minute} {hour} {day_of_month} "
                f"{month_of_year} {day_of_week} ({timezone})"
            )

        return schedule
