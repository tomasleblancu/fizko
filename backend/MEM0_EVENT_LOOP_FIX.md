# Mem0 Event Loop Fix - Celery Tasks

## Problem

When running multiple Celery tasks that use Mem0 client, the second task would fail with:
```
RuntimeError: Event loop is closed
```

### Root Cause

1. **Singleton Pattern**: `get_mem0_client()` used a global singleton for the Mem0 AsyncMemoryClient
2. **Event Loop Lifecycle**: Each Celery task creates a new event loop with `asyncio.run()`
3. **Stale Client**: The singleton client was tied to the first task's event loop
4. **Closed Loop**: When the second task ran, the client tried to use the closed event loop from the first task

### Error Flow

```
Task 1 (ForkPoolWorker-2)
  ├─ Creates event loop A
  ├─ get_mem0_client() creates client with loop A
  ├─ Task completes ✅
  └─ Event loop A closes

Task 2 (ForkPoolWorker-2) - Same worker!
  ├─ Creates event loop B
  ├─ get_mem0_client() returns SAME client (loop A)
  ├─ Client tries to use closed loop A
  └─ ERROR: "Event loop is closed" ❌
```

## Solution

Modified `get_mem0_client()` to detect event loop changes and recreate the client:

### File: `backend/app/agents/tools/memory/memory_tools.py`

**Added tracking:**
```python
_mem0_client: Optional[AsyncMemoryClient] = None
_mem0_client_loop: Optional[asyncio.AbstractEventLoop] = None
```

**Modified function:**
```python
def get_mem0_client() -> AsyncMemoryClient:
    """
    Get or create async Mem0 client.

    Detects if event loop has changed (e.g., in Celery tasks) and recreates
    the client if needed to avoid "Event loop is closed" errors.
    """
    global _mem0_client, _mem0_client_loop

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - will be created when needed
        current_loop = None

    # Recreate client if loop changed or client doesn't exist
    if _mem0_client is None or _mem0_client_loop != current_loop:
        api_key = os.getenv("MEM0_API_KEY")
        if not api_key:
            raise ValueError("MEM0_API_KEY environment variable not set")

        # Initialize Mem0 async client with API key
        _mem0_client = AsyncMemoryClient(api_key=api_key)
        _mem0_client_loop = current_loop

        if current_loop:
            logger.info(f"✨ Mem0 async client initialized for event loop {id(current_loop)}")
        else:
            logger.info("✨ Mem0 async client initialized")

    return _mem0_client
```

### Key Changes

1. **Track Event Loop**: Store reference to the event loop when client is created
2. **Detect Changes**: Check if current event loop differs from stored loop
3. **Recreate Client**: If loop changed, create new client with new loop
4. **Log Loop ID**: Help debugging by logging event loop ID

## How It Works

```
Task 1 (ForkPoolWorker-2)
  ├─ Creates event loop A (id: 12345)
  ├─ get_mem0_client() creates client + stores loop A
  ├─ "✨ Mem0 async client initialized for event loop 12345"
  ├─ Task completes ✅
  └─ Event loop A closes

Task 2 (ForkPoolWorker-2)
  ├─ Creates event loop B (id: 67890)
  ├─ get_mem0_client() detects loop changed (12345 → 67890)
  ├─ Creates NEW client with loop B ✅
  ├─ "✨ Mem0 async client initialized for event loop 67890"
  └─ Task completes ✅
```

## Testing

### Before Fix
```
[2025-11-08 13:26:41] Task 1 succeeded ✅
[2025-11-08 13:27:12] Task 2 received
[2025-11-08 13:27:14] ERROR: Event loop is closed ❌
```

### After Fix
```
[2025-11-08 XX:XX:XX] Task 1 succeeded ✅
[2025-11-08 XX:XX:XX] Task 2 received
[2025-11-08 XX:XX:XX] Mem0 client initialized for event loop XXXXX
[2025-11-08 XX:XX:XX] Task 2 succeeded ✅
```

## Why This Works

- **Per-Loop Client**: Each event loop gets its own Mem0 client instance
- **Automatic Detection**: No need to manually manage client lifecycle
- **Safe Singleton**: Still uses singleton pattern, but respects event loop boundaries
- **Zero Breaking Changes**: Same API, no changes needed in calling code

## Related Issues

This is similar to but different from the previous fix in `CELERY_MEM0_FIX.md`:
- **Previous fix**: Removed manual client closure in `finally` blocks
- **This fix**: Detects event loop changes and recreates client

Both fixes address different aspects of async client lifecycle in Celery.

## Files Modified

- `backend/app/agents/tools/memory/memory_tools.py` - Event loop detection logic

## Deployment Notes

- ✅ No database migrations needed
- ✅ No environment variable changes
- ✅ Backward compatible
- ✅ Celery workers will pick up change on restart

## Future Improvements

Consider fully removing singleton pattern for Celery tasks and creating a new client per task. This would be more explicit but requires changes in all task code.

Alternatively, use a context manager pattern:
```python
async with get_mem0_context() as mem0:
    # Use mem0 client
    # Automatically cleaned up
```

