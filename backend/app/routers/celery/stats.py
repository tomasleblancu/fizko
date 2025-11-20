"""
Statistics and monitoring endpoints for Celery router.

Handles:
- Getting Celery worker statistics
- Monitoring active tasks
- Queue statistics
"""
import logging
from fastapi import APIRouter, HTTPException

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
async def get_celery_stats():
    """
    Get Celery worker and queue statistics.

    Returns:
        - active_tasks: Number of currently executing tasks
        - scheduled_tasks: Number of tasks waiting to execute
        - registered_tasks: List of registered task names
        - workers: List of active workers and their status

    Example response:
        ```json
        {
            "active_tasks": {
                "celery@worker1": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "sii.sync_documents",
                        "args": [],
                        "kwargs": {"company_id": "..."}
                    }
                ]
            },
            "scheduled_tasks": {},
            "registered_tasks": ["sii.sync_documents", ...],
            "worker_stats": {
                "celery@worker1": {
                    "total": 156,
                    "pool": {
                        "max-concurrency": 4,
                        "processes": [12345, 12346, 12347, 12348]
                    }
                }
            }
        }
        ```
    """
    try:
        # Get active tasks
        inspect = celery_app.control.inspect()

        active = inspect.active()
        scheduled = inspect.scheduled()
        registered = inspect.registered()
        stats = inspect.stats()

        return {
            "active_tasks": active,
            "scheduled_tasks": scheduled,
            "registered_tasks": registered,
            "worker_stats": stats,
        }

    except Exception as e:
        logger.error(f"❌ Failed to get Celery stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Celery stats: {str(e)}"
        )
