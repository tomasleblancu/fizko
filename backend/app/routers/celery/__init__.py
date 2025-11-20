"""
Celery Tasks Router for Backend V2.

Modular router for managing Celery tasks via REST API.

Structure:
    celery/
    ├── __init__.py     # Main router (this file)
    ├── models.py       # Pydantic models and enums
    ├── tasks.py        # Task listing and launching
    ├── status.py       # Task status monitoring
    └── stats.py        # Celery statistics

Provides endpoints to:
- Launch Celery tasks and get task IDs
- Query task status and results
- List available tasks
- Revoke/cancel running tasks
- Get Celery worker statistics

This router allows external services to trigger and monitor
background tasks without direct access to the Celery infrastructure.

Example:
    ```python
    # Launch a task
    response = requests.post("/api/celery/tasks/launch", json={
        "task_type": "sii.sync_documents",
        "params": {"company_id": "123", "months": 1}
    })
    task_id = response.json()["task_id"]

    # Check status
    status = requests.get(f"/api/celery/tasks/{task_id}")
    print(status.json()["status"])  # PENDING, STARTED, SUCCESS, etc.
    ```
"""
from fastapi import APIRouter

from . import tasks
from . import status
from . import stats

# Create main router with prefix and tags
router = APIRouter(
    prefix="/celery",
    tags=["Celery Tasks"],
)

# Include sub-routers
router.include_router(tasks.router)
router.include_router(status.router)
router.include_router(stats.router)

# Export router
__all__ = ["router"]
