"""
Router for Celery task management and monitoring.

Provides endpoints to:
- Submit tasks to Celery
- Check task status
- Get task results
"""
import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ========== Request/Response Models ==========


class TaskSubmitResponse(BaseModel):
    """Response when submitting a task"""

    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Initial task status (usually 'PENDING')")
    message: str = Field(..., description="Human-readable message")


class TaskStatusResponse(BaseModel):
    """Response for task status check"""

    task_id: str
    status: str = Field(
        ...,
        description="Task status: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED",
    )
    result: Optional[Any] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    traceback: Optional[str] = Field(None, description="Traceback if failed")


class DocumentSyncRequest(BaseModel):
    """Request to sync tax documents (purchases and sales)"""

    session_id: str = Field(..., description="SII session UUID")
    months: int = Field(1, ge=1, le=12, description="Number of months to sync (1-12)")


# ========== Task Status Endpoint ==========


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get task status",
)
async def get_task_status(
    task_id: str,
    current_user_id: UUID = Depends(get_current_user_id),
) -> TaskStatusResponse:
    """
    Get the status of a Celery task.

    Returns the current status and result (if completed) of a task.
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
            traceback=None,
        )

        if task.successful():
            response.result = task.result
        elif task.failed():
            response.error = str(task.info)
            response.traceback = task.traceback

        return response

    except Exception as e:
        logger.error(f"❌ Error getting task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting task status: {str(e)}",
        )


# ========== SII Task Endpoints ==========


@router.post(
    "/sii/sync-documents",
    response_model=TaskSubmitResponse,
    summary="Submit documents sync task",
)
async def submit_documents_sync(
    request: DocumentSyncRequest,
    current_user_id: UUID = Depends(get_current_user_id),
) -> TaskSubmitResponse:
    """
    Submit a task to sync tax documents (purchases and sales) from SII.

    This task syncs both purchase and sale documents for the last N months.
    The task runs in the background via Celery and can take several minutes
    depending on the number of documents.

    Use GET /api/tasks/status/{task_id} to check progress.

    Example:
        POST /api/tasks/sii/sync-documents
        {
            "session_id": "359c515e-9e02-44ba-85e7-6aad24d6e2e1",
            "months": 1
        }

        Response:
        {
            "task_id": "abc123-456-789...",
            "status": "PENDING",
            "message": "Documents sync task submitted successfully. Syncing 1 month(s)."
        }
    """
    try:
        from app.infrastructure.celery.tasks.sii import sync_documents

        task = sync_documents.delay(
            session_id=request.session_id,
            months=request.months,
        )

        logger.info(f"✅ Documents sync task submitted: {task.id}")

        return TaskSubmitResponse(
            task_id=task.id,
            status="PENDING",
            message=f"Documents sync task submitted successfully. Syncing {request.months} month(s).",
        )

    except Exception as e:
        logger.error(f"❌ Error submitting documents sync task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting task: {str(e)}",
        )
