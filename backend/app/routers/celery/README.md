# Celery Router Module

Modular router for managing Celery tasks via REST API in Backend V2.

## Structure

```
celery/
├── __init__.py     # Main router that combines all sub-routers
├── models.py       # Pydantic models and enums
├── tasks.py        # Task listing and launching endpoints
├── status.py       # Task status monitoring endpoints
├── stats.py        # Celery statistics endpoints
└── README.md       # This file
```

## Modules

### `models.py`
Contains all Pydantic models and enums used by the router:

**Enums:**
- `TaskType` - Available task types (SYNC_DOCUMENTS, SYNC_F29, etc.)
- `TaskStatus` - Celery task states (PENDING, STARTED, SUCCESS, FAILURE, etc.)

**Parameter Models:**
- `SyncDocumentsParams` - Parameters for document sync task
- `SyncDocumentsAllParams` - Parameters for batch document sync
- `SyncF29Params` - Parameters for F29 sync task
- `SyncF29AllParams` - Parameters for batch F29 sync

**Request/Response Models:**
- `TaskLaunchRequest` - Request to launch a task
- `TaskLaunchResponse` - Response with task ID
- `TaskStatusResponse` - Response with task status and result
- `AvailableTask` - Information about an available task

### `tasks.py`
Endpoints for task management:

- **GET /api/celery/tasks** - List all available tasks
- **POST /api/celery/tasks/launch** - Launch a new task

**Example:**
```python
from fastapi import APIRouter
from .tasks import router as tasks_router

# The router is already configured with endpoints
```

### `status.py`
Endpoints for task monitoring:

- **GET /api/celery/tasks/{task_id}** - Get task status and result
- **DELETE /api/celery/tasks/{task_id}** - Revoke/cancel a task
- **POST /api/celery/tasks/{task_id}/retry** - Retry a failed task

**Example:**
```python
# Query task status
GET /api/celery/tasks/550e8400-e29b-41d4-a716-446655440000

# Response
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "SUCCESS",
    "result": {"compras": {"total": 150}, ...},
    "error": null,
    "traceback": null,
    "meta": null
}
```

### `stats.py`
Endpoints for Celery monitoring:

- **GET /api/celery/stats** - Get worker and queue statistics

**Example:**
```python
# Get Celery stats
GET /api/celery/stats

# Response
{
    "active_tasks": {...},
    "scheduled_tasks": {...},
    "registered_tasks": [...],
    "worker_stats": {...}
}
```

### `__init__.py`
Main router that combines all sub-routers:

```python
from fastapi import APIRouter

from . import tasks
from . import status
from . import stats

router = APIRouter(
    prefix="/celery",
    tags=["Celery Tasks"],
)

router.include_router(tasks.router)
router.include_router(status.router)
router.include_router(stats.router)
```

## Usage in Main Application

In `app/main.py`:

```python
from app.routers import celery

app.include_router(celery.router, prefix="/api")
```

This will make all endpoints available under `/api/celery/*`.

## Adding New Endpoints

### 1. Add to Appropriate Module

If adding a new endpoint, decide which module it belongs to:
- Task-related → `tasks.py`
- Status-related → `status.py`
- Statistics-related → `stats.py`

### 2. Add Models (if needed)

If your endpoint needs new request/response models, add them to `models.py`:

```python
class NewTaskParams(BaseModel):
    """Parameters for new task"""
    param1: str = Field(..., description="Parameter 1")
    param2: int = Field(1, ge=1, description="Parameter 2")
```

### 3. Implement Endpoint

Add the endpoint to the appropriate router:

```python
@router.post("/tasks/new-action")
async def new_action(params: NewTaskParams):
    """
    New action description.
    """
    # Implementation
    return {"status": "ok"}
```

### 4. Update Documentation

Update this README and the main API documentation in `backend-v2/CELERY_TASKS_API.md`.

## Testing

### Unit Testing

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_tasks():
    response = client.get("/api/celery/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) > 0
```

### Integration Testing

See `backend-v2/test_celery_api.py` for a complete example.

## Error Handling

All endpoints follow consistent error handling:

- **400 Bad Request** - Invalid parameters or wrong task type
- **422 Unprocessable Entity** - Pydantic validation errors
- **500 Internal Server Error** - Celery connection errors or other exceptions

Example error response:
```json
{
    "detail": "Failed to launch task: Redis connection refused"
}
```

## Logging

All endpoints include structured logging:

```python
logger.info(f"📤 Launching task: {task_type}")
logger.error(f"❌ Failed to launch task: {e}", exc_info=True)
```

Logs use emojis for easy visual scanning:
- 📤 - Outgoing operations (launching tasks)
- 📊 - Status queries
- ✅ - Success
- ❌ - Errors
- 🚫 - Cancellations

## Dependencies

The router depends on:
- `app.infrastructure.celery.celery_app` - Celery application instance
- `app.infrastructure.celery.tasks.sii` - SII task implementations
- FastAPI and Pydantic for API framework

## Future Enhancements

Potential improvements for this module:

1. **Task History** - Store and query historical task executions
2. **Batch Operations** - Launch multiple tasks in one request
3. **Task Prioritization** - Allow setting task priority levels
4. **Webhooks** - Notify external services when tasks complete
5. **Task Scheduling** - Schedule tasks for future execution
6. **Result Caching** - Cache task results in Redis
7. **Rate Limiting** - Prevent task queue overload

## Related Documentation

- [CELERY_TASKS_API.md](../../../CELERY_TASKS_API.md) - Complete API documentation
- [test_celery_api.py](../../../test_celery_api.py) - Test script
- [Celery Infrastructure README](../../../app/infrastructure/celery/README.md) - Celery setup
