"""
Generic Celery Task Launch Endpoint

Provides a single endpoint to launch various Celery tasks with a unified interface.
"""
import logging
from typing import Any, Dict, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["celery-tasks"]
)


# ========== Request/Response Models ==========

CeleryTaskType = Literal[
    "sii.sync_documents",
    "sii.sync_documents_all_companies",
    "sii.sync_f29",
    "sii.sync_f29_all_companies",
    "calendar.sync_company_calendar",
    "calendar.sync_all_companies_calendar",
]


class LaunchTaskRequest(BaseModel):
    """Request to launch a Celery task"""
    task_type: CeleryTaskType = Field(..., description="Type of task to launch")
    params: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")


class LaunchTaskResponse(BaseModel):
    """Response from launching a task"""
    success: bool = Field(..., description="Whether task was launched successfully")
    task_id: str = Field(..., description="Celery task ID")
    task_type: str = Field(..., description="Type of task launched")
    status: str = Field(..., description="Initial task status (usually 'pending')")
    message: str | None = Field(None, description="Human-readable message")


class TaskStatusResponse(BaseModel):
    """Response for task status check"""
    task_id: str
    status: str = Field(
        ...,
        description="Task status: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED",
    )
    result: Any | None = Field(None, description="Task result if completed")
    error: str | None = Field(None, description="Error message if failed")
    progress: int | None = Field(None, description="Progress percentage (0-100)")
    created_at: str | None = Field(None, description="Task creation timestamp")
    started_at: str | None = Field(None, description="Task start timestamp")
    completed_at: str | None = Field(None, description="Task completion timestamp")


# ========== Endpoints ==========

@router.post("/launch", response_model=LaunchTaskResponse)
async def launch_task(
    request: LaunchTaskRequest,
    current_user_id: UUID = Depends(get_current_user_id),
) -> LaunchTaskResponse:
    """
    Launch a Celery task

    This is a generic endpoint that can launch various types of Celery tasks.
    Each task type expects different parameters in the `params` field.

    **Task Types and Parameters:**

    - `sii.sync_documents`: Sync SII documents
        - `company_id` (str): Company UUID
        - `months` (int): Number of months to sync
        - `month_offset` (int, optional): Month offset from current month

    - `sii.sync_f29`: Sync Form29
        - `company_id` (str): Company UUID
        - `year` (str, optional): Year in YYYY format

    - `calendar.sync_company_calendar`: Sync company calendar events
        - `company_id` (str): Company UUID

    **Example:**
        ```json
        {
            "task_type": "calendar.sync_company_calendar",
            "params": {
                "company_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
        ```

    **Returns:**
        Task launch response with task_id for tracking
    """
    try:
        logger.info(f"🚀 Launching task: {request.task_type}")
        logger.info(f"📋 Parameters: {request.params}")

        # Import Celery app
        from app.infrastructure.celery import celery_app

        # Map task types to Celery task names
        task_map = {
            "sii.sync_documents": "sii.sync_documents",
            "sii.sync_documents_all_companies": "sii.sync_documents_all_companies",
            "sii.sync_f29": "sii.sync_f29",
            "sii.sync_f29_all_companies": "sii.sync_f29_all_companies",
            "calendar.sync_company_calendar": "calendar.sync_company_calendar",
            "calendar.sync_all_companies_calendar": "calendar.sync_all_companies_calendar",
        }

        celery_task_name = task_map.get(request.task_type)
        if not celery_task_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown task type: {request.task_type}"
            )

        # Launch the task
        task = celery_app.send_task(
            celery_task_name,
            kwargs=request.params
        )

        logger.info(f"✅ Task launched successfully: {task.id}")

        return LaunchTaskResponse(
            success=True,
            task_id=task.id,
            task_type=request.task_type,
            status="pending",
            message=f"Task {request.task_type} launched successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error launching task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error launching task: {str(e)}"
        )


@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user_id: UUID = Depends(get_current_user_id),
) -> TaskStatusResponse:
    """
    Get the status of a Celery task

    Returns the current status and result (if completed) of a task.

    **Possible statuses:**
    - `PENDING`: Task is waiting to be executed
    - `STARTED`: Task has started running
    - `SUCCESS`: Task completed successfully
    - `FAILURE`: Task failed with an error
    - `RETRY`: Task is being retried
    - `REVOKED`: Task was cancelled

    **Returns:**
        Task status with result or error details
    """
    try:
        from celery.result import AsyncResult
        from app.infrastructure.celery import celery_app

        task = AsyncResult(task_id, app=celery_app)

        # Build response
        response = TaskStatusResponse(
            task_id=task_id,
            status=task.status,
            result=None,
            error=None,
            progress=None,
            created_at=None,
            started_at=None,
            completed_at=None,
        )

        if task.successful():
            response.result = task.result
            response.progress = 100
        elif task.failed():
            response.error = str(task.info)
        elif task.status == "PENDING":
            response.progress = 0
        elif task.status == "STARTED":
            # Try to get progress from task info
            if isinstance(task.info, dict):
                response.progress = task.info.get("progress", 0)

        return response

    except Exception as e:
        logger.error(f"❌ Error getting task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting task status: {str(e)}",
        )


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, bool]:
    """
    Cancel a running Celery task

    Attempts to revoke/cancel a running task. Note that this may not
    stop tasks that are already executing, depending on the task type.

    **Returns:**
        ```json
        {
            "success": true
        }
        ```
    """
    try:
        from celery.result import AsyncResult
        from app.infrastructure.celery import celery_app

        task = AsyncResult(task_id, app=celery_app)
        task.revoke(terminate=True)

        logger.info(f"✅ Task cancelled: {task_id}")

        return {"success": True}

    except Exception as e:
        logger.error(f"❌ Error cancelling task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling task: {str(e)}",
        )
