"""
Task management endpoints for Celery router.

Handles:
- Listing available tasks
- Launching tasks
- Getting task descriptions
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException

from app.infrastructure.celery.tasks.sii import (
    sync_documents,
    sync_documents_all_companies,
    sync_f29,
    sync_f29_all_companies,
)
from app.infrastructure.celery.tasks.calendar import sync_company_calendar
from .models import (
    TaskType,
    TaskLaunchRequest,
    TaskLaunchResponse,
    AvailableTask,
    SyncDocumentsParams,
    SyncDocumentsAllParams,
    SyncF29Params,
    SyncF29AllParams,
    SyncCompanyCalendarParams,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tasks", response_model=List[AvailableTask])
async def list_available_tasks():
    """
    List all available Celery tasks with their descriptions.

    This endpoint helps clients discover what tasks can be launched.
    """
    return [
        AvailableTask(
            task_type=TaskType.SYNC_DOCUMENTS.value,
            name="sii.sync_documents",
            description="Sync tax documents (purchases, sales, honorarios) for a single company",
            parameters={
                "company_id": {"type": "string", "required": True, "description": "Company UUID"},
                "months": {"type": "integer", "required": False, "default": 1, "min": 1, "max": 12},
                "month_offset": {"type": "integer", "required": False, "default": 0, "min": 0},
            }
        ),
        AvailableTask(
            task_type=TaskType.SYNC_DOCUMENTS_ALL.value,
            name="sii.sync_documents_all_companies",
            description="Sync documents for ALL companies with active subscriptions",
            parameters={
                "months": {"type": "integer", "required": False, "default": 1},
                "month_offset": {"type": "integer", "required": False, "default": 0},
            }
        ),
        AvailableTask(
            task_type=TaskType.SYNC_F29.value,
            name="sii.sync_f29",
            description="Sync F29 forms for a single company",
            parameters={
                "company_id": {"type": "string", "required": True, "description": "Company UUID"},
                "year": {"type": "string", "required": False, "default": "current year", "description": "Year to sync (YYYY format)"},
            }
        ),
        AvailableTask(
            task_type=TaskType.SYNC_F29_ALL.value,
            name="sii.sync_f29_all_companies",
            description="Sync F29 forms for ALL companies",
            parameters={
                "year": {"type": "string", "required": False, "default": "current year", "description": "Year to sync (YYYY format)"},
            }
        ),
        AvailableTask(
            task_type=TaskType.SYNC_COMPANY_CALENDAR.value,
            name="calendar.sync_company_calendar",
            description="Sync calendar events for a company based on active event templates",
            parameters={
                "company_id": {"type": "string", "required": True, "description": "Company UUID"},
            }
        ),
    ]


@router.post("/tasks/launch", response_model=TaskLaunchResponse)
async def launch_task(request: TaskLaunchRequest):
    """
    Launch a Celery task and get its task ID.

    Use the returned task_id to query task status via GET /celery/tasks/{task_id}

    Example:
        ```json
        {
            "task_type": "sii.sync_documents",
            "params": {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "months": 3,
                "month_offset": 0
            }
        }
        ```
    """
    try:
        logger.info(f"📤 Launching task: {request.task_type} with params: {request.params}")

        # Dispatch to appropriate task based on task_type
        task_result = None

        if request.task_type == TaskType.SYNC_DOCUMENTS:
            # Validate params
            params = SyncDocumentsParams(**request.params)
            task_result = sync_documents.apply_async(
                kwargs={
                    "company_id": params.company_id,
                    "months": params.months,
                    "month_offset": params.month_offset,
                }
            )

        elif request.task_type == TaskType.SYNC_DOCUMENTS_ALL:
            params = SyncDocumentsAllParams(**request.params)
            task_result = sync_documents_all_companies.apply_async(
                kwargs={
                    "months": params.months,
                    "month_offset": params.month_offset,
                }
            )

        elif request.task_type == TaskType.SYNC_F29:
            params = SyncF29Params(**request.params)
            kwargs = {"company_id": params.company_id}
            if params.year:
                kwargs["year"] = params.year
            task_result = sync_f29.apply_async(kwargs=kwargs)

        elif request.task_type == TaskType.SYNC_F29_ALL:
            params = SyncF29AllParams(**request.params)
            kwargs = {}
            if params.year:
                kwargs["year"] = params.year
            task_result = sync_f29_all_companies.apply_async(kwargs=kwargs)

        elif request.task_type == TaskType.SYNC_COMPANY_CALENDAR:
            params = SyncCompanyCalendarParams(**request.params)
            task_result = sync_company_calendar.apply_async(
                kwargs={"company_id": params.company_id}
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task type: {request.task_type}"
            )

        logger.info(f"✅ Task launched successfully: {task_result.id}")

        return TaskLaunchResponse(
            success=True,
            task_id=task_result.id,
            task_type=request.task_type.value,
            status=task_result.status,
            message=f"Task {request.task_type.value} launched successfully"
        )

    except ValueError as e:
        # Pydantic validation error
        logger.error(f"❌ Invalid parameters: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"❌ Failed to launch task: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch task: {str(e)}"
        )
