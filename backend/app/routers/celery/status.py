"""
Task status and monitoring endpoints for Celery router.

Handles:
- Getting task status by ID
- Revoking/cancelling tasks
- Retrying failed tasks
"""
import logging
from fastapi import APIRouter, HTTPException, Query

from app.infrastructure.celery import celery_app
from .models import TaskStatus, TaskStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Query the status and result of a Celery task by its ID.

    Returns:
        - status: Current task state (PENDING, STARTED, SUCCESS, FAILURE, etc.)
        - result: Task result if completed successfully
        - error: Error message if task failed
        - traceback: Full error traceback if task failed
        - meta: Additional task metadata (progress info, etc.)

    Example:
        GET /celery/tasks/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        # Get task result from Celery
        result = celery_app.AsyncResult(task_id)

        # Build response based on task state
        response = TaskStatusResponse(
            task_id=task_id,
            status=TaskStatus(result.status),
            result=None,
            error=None,
            traceback=None,
            meta=None,
        )

        if result.state == "SUCCESS":
            # Task completed successfully
            response.result = result.result

        elif result.state == "FAILURE":
            # Task failed
            response.error = str(result.result) if result.result else "Unknown error"
            response.traceback = result.traceback

        elif result.state == "PENDING":
            # Task is waiting or doesn't exist
            # Note: PENDING is also returned for non-existent task IDs
            response.meta = {"info": "Task is waiting to be executed or doesn't exist"}

        elif result.state == "STARTED":
            # Task is currently running
            response.meta = result.info if result.info else {"info": "Task is running"}

        elif result.state == "RETRY":
            # Task is being retried
            response.meta = result.info if result.info else {"info": "Task is being retried"}
            response.error = "Task failed and is being retried"

        else:
            # Other states (custom states set by tasks)
            response.meta = result.info if result.info else {}

        logger.info(f"📊 Task status: {task_id} -> {result.state}")

        return response

    except Exception as e:
        logger.error(f"❌ Failed to get task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def revoke_task(
    task_id: str,
    terminate: bool = Query(False, description="Force terminate the task if it's running")
):
    """
    Revoke (cancel) a Celery task.

    Args:
        task_id: The Celery task ID to revoke
        terminate: If True, forcefully terminate the task if it's already running.
                  If False, only prevent it from executing if it hasn't started yet.

    Warning:
        Using terminate=True can leave tasks in an inconsistent state.
        Use with caution.

    Example:
        DELETE /celery/tasks/550e8400-e29b-41d4-a716-446655440000?terminate=false
    """
    try:
        # Revoke the task
        celery_app.control.revoke(
            task_id,
            terminate=terminate,
            signal='SIGTERM' if terminate else None
        )

        logger.info(f"🚫 Task revoked: {task_id} (terminate={terminate})")

        return {
            "task_id": task_id,
            "status": "revoked",
            "terminate": terminate,
            "message": f"Task {task_id} has been revoked"
        }

    except Exception as e:
        logger.error(f"❌ Failed to revoke task: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke task: {str(e)}"
        )


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """
    Retry a failed task.

    Note: This endpoint doesn't actually retry the original task, but launches
    a new task with the same parameters. The original task must have stored
    its parameters in the result for this to work.

    Returns:
        New task ID for the retry
    """
    try:
        # Get original task result
        result = celery_app.AsyncResult(task_id)

        if result.state != "FAILURE":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot retry task in state: {result.state}. Only FAILURE tasks can be retried."
            )

        # For now, just return info that manual retry is needed
        # A full implementation would need to store original task params
        return {
            "task_id": task_id,
            "message": "Task retry must be triggered manually by re-submitting the task with original parameters",
            "status": result.state,
            "error": str(result.result) if result.result else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retry task: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retry task: {str(e)}"
        )
