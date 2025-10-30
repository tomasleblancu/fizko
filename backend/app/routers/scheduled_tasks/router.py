"""
API Router for managing Celery Beat scheduled tasks.

This module provides HTTP endpoints that delegate business logic to services.
The router is responsible ONLY for:
- HTTP request/response handling
- Schema validation (via Pydantic)
- Error mapping to HTTP status codes
- Dependency injection

All business logic is in app.services.scheduled_tasks.
"""

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.services.scheduled_tasks import BeatService, SchedulerService

from .dependencies import get_user_company_id
from .schemas import (
    ScheduledTaskCreate,
    ScheduledTaskResponse,
    ScheduledTaskUpdate,
    TaskExecutionResponse,
)
from .utils import format_task_response

router = APIRouter(prefix="/scheduled-tasks", tags=["Scheduled Tasks"])


# ============================================================================
# Dependency Injection - Service Factories
# ============================================================================


def get_scheduler_service(db: AsyncSession = Depends(get_db)) -> SchedulerService:
    """Dependency to get SchedulerService instance."""
    return SchedulerService(db)


def get_beat_service(db: AsyncSession = Depends(get_db)) -> BeatService:
    """Dependency to get BeatService instance."""
    return BeatService(db)


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/available-tasks", response_model=List[Dict[str, Any]])
async def get_available_tasks(
    beat_service: BeatService = Depends(get_beat_service),
) -> List[Dict[str, Any]]:
    """
    Get all registered Celery tasks that can be scheduled.

    Returns a list of available tasks with their names and descriptions.
    This allows the frontend to dynamically populate the task selector.
    """
    return beat_service.get_available_tasks()


@router.post("", response_model=ScheduledTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_task(
    request: ScheduledTaskCreate,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduledTaskResponse:
    """
    Create a new scheduled task.

    Note: Tasks created via this endpoint are system-level tasks (company_id = NULL).
    To create company-specific tasks, use a different endpoint or specify company_id.

    Creates a periodic task that will be executed by Celery Beat according
    to the specified schedule (interval or crontab).
    """
    try:
        task = await scheduler_service.create_scheduled_task(
            request=request, company_id=None  # System-level task
        )
        return format_task_response(task)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[ScheduledTaskResponse])
async def list_scheduled_tasks(
    enabled: bool | None = None,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> List[ScheduledTaskResponse]:
    """
    List all system-level scheduled tasks.

    Query Parameters:
        enabled: Optional filter by enabled status (true/false)

    Note: Only system-level tasks (company_id IS NULL) are returned.
    Company-specific tasks are managed elsewhere.
    """
    tasks = await scheduler_service.list_scheduled_tasks(
        enabled=enabled, company_id=None  # System-level tasks only
    )
    return [format_task_response(task) for task in tasks]


@router.get("/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(
    task_id: int,
    company_id: UUID = Depends(get_user_company_id),
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduledTaskResponse:
    """
    Get details of a specific scheduled task.

    The task must belong to the user's company (multi-tenancy check).
    """
    task = await scheduler_service.get_scheduled_task(task_id=task_id, company_id=company_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found or access denied",
        )

    return format_task_response(task)


@router.put("/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: int,
    request: ScheduledTaskUpdate,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduledTaskResponse:
    """
    Update an existing scheduled task.

    Note: You cannot change the schedule type or schedule parameters.
    To change the schedule, delete the task and create a new one.

    Only system-level tasks (company_id = NULL) can be updated via this endpoint.
    """
    task = await scheduler_service.update_scheduled_task(
        task_id=task_id, request=request, company_id=None  # System-level only
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System task with id {task_id} not found",
        )

    return format_task_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_task(
    task_id: int,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> None:
    """
    Delete a scheduled task.

    The task will be removed from the database and will no longer be executed.
    Celery Beat will detect the change automatically.

    Note: Only system-level tasks (company_id = NULL) can be deleted via this endpoint.
    """
    deleted = await scheduler_service.delete_scheduled_task(
        task_id=task_id, company_id=None  # System-level only
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System task with id {task_id} not found",
        )


@router.post("/{task_id}/enable", response_model=ScheduledTaskResponse)
async def enable_scheduled_task(
    task_id: int,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduledTaskResponse:
    """Enable a system-level scheduled task."""
    task = await scheduler_service.set_task_enabled(
        task_id=task_id, enabled=True, company_id=None  # System-level only
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System task with id {task_id} not found",
        )

    return format_task_response(task)


@router.post("/{task_id}/disable", response_model=ScheduledTaskResponse)
async def disable_scheduled_task(
    task_id: int,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduledTaskResponse:
    """Disable a system-level scheduled task."""
    task = await scheduler_service.set_task_enabled(
        task_id=task_id, enabled=False, company_id=None  # System-level only
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System task with id {task_id} not found",
        )

    return format_task_response(task)


@router.post("/{task_id}/run-now")
async def run_scheduled_task_now(
    task_id: int,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    beat_service: BeatService = Depends(get_beat_service),
) -> Dict[str, Any]:
    """
    Trigger a scheduled task immediately (outside its normal schedule).

    Returns the Celery task ID that can be used to check status.

    Note: Only system-level tasks (company_id = NULL) can be triggered via this endpoint.
    """
    # Get task (system-level only)
    task = await scheduler_service.get_scheduled_task(task_id=task_id, company_id=None)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System task with id {task_id} not found",
        )

    # Trigger task via Beat service
    try:
        result = await beat_service.trigger_task_now(task)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger task: {str(e)}",
        )


@router.get("/{task_id}/executions", response_model=List[TaskExecutionResponse])
async def get_task_executions(
    task_id: int,
    limit: int = 20,
    company_id: UUID = Depends(get_user_company_id),
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> List[TaskExecutionResponse]:
    """
    Get execution history for a scheduled task.

    Query Parameters:
        limit: Maximum number of executions to return (default: 20, max: 100)
    """
    executions = await scheduler_service.get_task_executions(
        task_id=task_id, limit=limit, company_id=company_id
    )

    if not executions:
        # Check if task exists to provide better error message
        task = await scheduler_service.get_scheduled_task(task_id=task_id, company_id=company_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found or access denied",
            )

    return [TaskExecutionResponse.model_validate(execution) for execution in executions]
