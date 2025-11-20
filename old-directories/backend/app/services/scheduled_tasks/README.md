# Scheduled Tasks Services

This package contains business logic for managing Celery Beat scheduled tasks, properly separated from HTTP routing concerns.

## Architecture

### Service Layer Pattern

The service layer encapsulates all business logic, database operations, and integration with Celery Beat. This follows the **separation of concerns** principle:

```
┌─────────────────┐
│   HTTP Router   │  → Only handles HTTP: validation, status codes, dependencies
└────────┬────────┘
         │ delegates to
         ↓
┌─────────────────┐
│    Services     │  → Business logic, database operations, Celery integration
└────────┬────────┘
         │ uses
         ↓
┌─────────────────┐
│  Models & DB    │  → Data persistence
└─────────────────┘
```

## Services

### `BeatService`

Handles all Celery Beat scheduler operations:

- `notify_schedule_changed()` - Notifies Beat to reload schedules from DB
- `trigger_task_now(task)` - Executes a scheduled task immediately
- `get_available_tasks()` - Lists all registered Celery tasks

**Usage:**
```python
from app.services.scheduled_tasks import BeatService

beat_service = BeatService(db)
await beat_service.notify_schedule_changed()
```

### `SchedulerService`

Manages scheduled task CRUD operations:

- `create_scheduled_task(request, company_id)` - Creates new periodic task
- `list_scheduled_tasks(enabled, company_id)` - Lists tasks with filters
- `get_scheduled_task(task_id, company_id)` - Gets single task
- `update_scheduled_task(task_id, request, company_id)` - Updates task
- `delete_scheduled_task(task_id, company_id)` - Deletes task
- `set_task_enabled(task_id, enabled, company_id)` - Enable/disable task
- `get_task_executions(task_id, limit, company_id)` - Gets execution history

**Usage:**
```python
from app.services.scheduled_tasks import SchedulerService
from app.routers.scheduled_tasks.schemas import ScheduledTaskCreate

scheduler = SchedulerService(db)

# Create task
request = ScheduledTaskCreate(
    name="daily-sync",
    task="sii.sync_documents",
    schedule_type="interval",
    interval_every=1,
    interval_period="days"
)
task = await scheduler.create_scheduled_task(request, company_id=None)

# List tasks
tasks = await scheduler.list_scheduled_tasks(enabled=True)
```

## Benefits of Service Layer

### 1. **Testability**
Services can be tested independently without HTTP layer:
```python
# Test service directly without FastAPI
async def test_create_task():
    service = SchedulerService(mock_db)
    task = await service.create_scheduled_task(request)
    assert task.name == "test-task"
```

### 2. **Reusability**
Services can be used from:
- HTTP endpoints (FastAPI routers)
- CLI commands
- Background tasks (Celery)
- Admin scripts
- Other services

### 3. **Single Responsibility**
- **Router**: HTTP request/response, validation, status codes
- **Service**: Business logic, database operations, integrations
- **Models**: Data structure and persistence

### 4. **Maintainability**
Changes to business logic don't affect HTTP layer and vice versa.

### 5. **Clarity**
Each layer has a clear, focused responsibility.

## Migration from Old Architecture

**Before (Router with embedded logic):**
```python
@router.post("")
async def create_task(request, db):
    # 100+ lines of business logic here
    # - Database queries
    # - Schedule creation
    # - Celery integration
    # - Notification logic
    pass
```

**After (Router delegates to Service):**
```python
@router.post("")
async def create_task(
    request,
    service: SchedulerService = Depends(get_scheduler_service)
):
    try:
        task = await service.create_scheduled_task(request)
        return format_task_response(task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

Much cleaner! The router now focuses on HTTP concerns only.

## Multi-tenancy Support

Both services support multi-tenancy via `company_id`:

- `company_id=None` → System-level tasks (global)
- `company_id=UUID` → Company-specific tasks

```python
# System task
await scheduler.create_scheduled_task(request, company_id=None)

# Company task
await scheduler.create_scheduled_task(request, company_id=company_uuid)
```

## Error Handling

Services raise Python exceptions:
- `ValueError` - Invalid input or business rule violation

Routers convert these to HTTP errors:
- `ValueError` → `400 Bad Request`
- `None` (not found) → `404 Not Found`
- Other exceptions → `500 Internal Server Error`

## Dependencies

Services receive database session via dependency injection:

```python
def get_scheduler_service(db: AsyncSession = Depends(get_db)):
    return SchedulerService(db)
```

This makes testing easy (inject mock DB) and keeps code clean.
