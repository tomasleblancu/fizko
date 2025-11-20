"""
Service for interacting with Celery Beat scheduler.

This service handles all Celery-specific operations including:
- Notifying Beat about schedule changes
- Triggering tasks immediately
- Listing available Celery tasks
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.scheduled_tasks import PeriodicTask, PeriodicTaskChanged

logger = logging.getLogger(__name__)


class BeatService:
    """Service for Celery Beat scheduler operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize BeatService.

        Args:
            db: Database session for operations
        """
        self.db = db

    async def notify_schedule_changed(self) -> None:
        """
        Notify Celery Beat that the schedule has changed.

        This updates the celery_periodictaskchanged table, which Beat monitors
        to detect when it needs to reload the schedule from the database.

        Beat checks this table every few seconds (maxinterval=5s by default).
        When it detects a change, it automatically reloads all tasks without restart.
        """
        # Check if there's already a record
        result = await self.db.execute(select(PeriodicTaskChanged).limit(1))
        changed_record = result.scalar_one_or_none()

        if changed_record:
            # Update existing record with current timestamp
            changed_record.last_update = datetime.utcnow()
        else:
            # Create new record
            changed_record = PeriodicTaskChanged(last_update=datetime.utcnow())
            self.db.add(changed_record)

        await self.db.flush()
        logger.debug("Notified Celery Beat of schedule change")

    async def trigger_task_now(self, task: PeriodicTask) -> Dict[str, Any]:
        """
        Trigger a scheduled task immediately (outside its normal schedule).

        Args:
            task: The PeriodicTask to execute

        Returns:
            Dict with task execution details including Celery task ID

        Raises:
            Exception: If task submission to Celery fails
        """
        from app.infrastructure.celery import celery_app

        # Parse args and kwargs from JSON strings
        try:
            args = json.loads(task.args) if isinstance(task.args, str) else task.args
        except (json.JSONDecodeError, TypeError):
            args = []

        try:
            kwargs = json.loads(task.kwargs) if isinstance(task.kwargs, str) else task.kwargs
        except (json.JSONDecodeError, TypeError):
            kwargs = {}

        # Submit task to Celery
        logger.info(f"Triggering task '{task.name}' (task={task.task}) manually")
        celery_task = celery_app.send_task(
            task.task,
            args=args,
            kwargs=kwargs,
            queue=task.queue,
            priority=task.priority,
        )

        logger.info(f"Task '{task.name}' submitted with Celery ID: {celery_task.id}")

        return {
            "success": True,
            "message": f"Task '{task.name}' triggered",
            "celery_task_id": celery_task.id,
            "task_name": task.task,
        }

    @staticmethod
    def get_available_tasks() -> List[Dict[str, Any]]:
        """
        Get all registered Celery tasks that can be scheduled.

        Returns a list of available tasks with their names, descriptions, and default kwargs.
        This allows the frontend to dynamically populate the task selector and arguments.

        Returns:
            List of dicts with task metadata (name, description, default_kwargs)
        """
        from app.infrastructure.celery import celery_app
        import inspect

        # Get all registered tasks from Celery
        registered_tasks = celery_app.tasks

        # Define default kwargs for known tasks
        # This maps task names to their default argument templates
        TASK_DEFAULT_KWARGS = {
            "sii.sync_documents": {
                "session_id": "",
                "months": 1,
                "company_id": ""
            },
            "sii.sync_documents_all_companies": {
                "months": 1
            },
            "sii.sync_f29": {
                "session_id": "",
                "year": 2025,
                "company_id": ""
            },
            "sii.sync_f29_all_companies": {
                "year": 2025
            },
            "sii.sync_f29_pdfs_missing": {
                "session_id": "",
                "company_id": "",
                "max_per_company": 10
            },
            "sii.sync_f29_pdfs_missing_all_companies": {
                "max_per_company": 10
            },
        }

        # Define default args for known tasks (positional arguments)
        # Template-driven notifications use args, not kwargs
        TASK_DEFAULT_ARGS = {
            "notifications.process_template_notification": {
                "args": ["daily_business_summary"],  # template_code
                "examples": [
                    "daily_business_summary",
                    "weekly_business_summary",
                    "monthly_business_summary"
                ],
                "help": "Código del template de notificación a procesar. Ejemplos: daily_business_summary, weekly_business_summary"
            },
        }

        # Filter out Celery internal tasks and format the response
        available_tasks = []
        for task_name in sorted(registered_tasks.keys()):
            # Skip internal Celery tasks
            if task_name.startswith("celery."):
                continue

            task = registered_tasks[task_name]

            # Extract docstring for description
            description = ""
            if task.__doc__:
                # Get first line of docstring as description
                description = task.__doc__.strip().split("\n")[0]

            # Get default kwargs for this task
            default_kwargs = TASK_DEFAULT_KWARGS.get(task_name, {})

            # Get default args for this task (if any)
            default_args_info = TASK_DEFAULT_ARGS.get(task_name, None)

            task_info = {
                "name": task_name,
                "description": description,
                "default_kwargs": default_kwargs,
            }

            # Add args info if this task uses positional arguments
            if default_args_info:
                task_info["default_args"] = default_args_info["args"]
                task_info["args_examples"] = default_args_info.get("examples", [])
                task_info["args_help"] = default_args_info.get("help", "")

            available_tasks.append(task_info)

        logger.debug(f"Found {len(available_tasks)} available Celery tasks")
        return available_tasks
