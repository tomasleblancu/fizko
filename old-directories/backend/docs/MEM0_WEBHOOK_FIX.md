# Mem0 Webhook Fix - Duplicate Memory ID Handling

## Problem

The original Mem0 webhook handler at `/webhooks/mem0` was causing `IntegrityError` exceptions due to duplicate `memory_id` violations:

```
sqlalchemy.exc.IntegrityError: duplicate key value violates unique constraint "company_brain_memory_id_key"
DETAIL: Key (memory_id)=(44cf5f67-b55c-4400-8d74-ad66734b8b08) already exists.
```

### Root Cause

The webhook handler had a **faulty heuristic** for detecting which `CompanyBrain` records needed updating:

```python
# OLD CODE (BROKEN)
if brain.memory_id and ("-" in brain.memory_id or "evt_" in brain.memory_id):
    # This assumes hyphens indicate an event_id that needs updating
    # BUT: Both event_ids AND final memory_ids from Mem0 are UUIDs with hyphens!
```

This caused the handler to:
1. Try to update records that already had valid Mem0 memory IDs
2. Attempt to set the same `memory_id` on multiple records
3. Violate the unique constraint on `memory_id`

### Why It Happened

When Mem0 processes memories:
- It returns either an `id` (immediate creation) or `event_id` (pending)
- Both are UUIDs with the format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- The webhook sends ADD events with the final memory_id
- Multiple webhooks can arrive for the same memory (race conditions)

## Solution

The fix implements **idempotent webhook handling**:

```python
# NEW CODE (FIXED)
async def handle_memory_added(memory_id: str, user_id: str, event_data: Dict[str, Any]) -> None:
    """
    Handle ADD event from Mem0.

    Strategy:
    1. Check if this memory_id already exists in our database (idempotency)
    2. If it exists, log and return (safe to call multiple times)
    3. If not, this is a new memory - just log it
    """
    # Check if memory already exists
    existing = await repo.get_by_memory_id(memory_id)
    if existing:
        logger.info(f"Memory already exists - idempotent (slug: {existing.slug})")
        return

    # New memory - no action needed, just log
    logger.info(f"New memory created in Mem0 - memory_id: {memory_id}")
```

### Key Changes

1. **Idempotency**: Check if `memory_id` exists before any updates
2. **No heuristics**: Don't try to guess which records need updating
3. **Graceful handling**: Log and return early for duplicate webhooks
4. **Error handling**: Wrap in try/except to prevent crashes

## Testing

Run the test to verify the fix:

```bash
cd backend
.venv/bin/python -c "
import asyncio
from app.routers.webhooks import handle_memory_added

async def test():
    memory_id = '44cf5f67-b55c-4400-8d74-ad66734b8b08'
    user_id = 'company_bd17df70-8b63-486a-8ce0-61d6ef959031'

    # Call twice - should be idempotent
    await handle_memory_added(memory_id, user_id, {})
    await handle_memory_added(memory_id, user_id, {})
    print('✅ Test passed - no IntegrityError!')

asyncio.run(test())
"
```

## Expected Behavior

### Before Fix
```
❌ IntegrityError: duplicate key value violates unique constraint
```

### After Fix
```
✅ Memory already exists in database - memory_id: xxx, slug: yyy (idempotent)
```

## Related Files

- [backend/app/routers/webhooks.py](../app/routers/webhooks.py) - Webhook handler
- [backend/app/repositories/brain.py](../app/repositories/brain.py) - Brain repositories
- [backend/app/db/models/brain.py](../app/db/models/brain.py) - Brain models
- [backend/supabase/migrations/028_create_brain_tables.sql](../supabase/migrations/028_create_brain_tables.sql) - Schema

## Future Considerations

Currently, the webhook handler is **read-only** for ADD events:
- It checks if the memory exists (idempotency)
- It doesn't create new records (memories are created via the API)

If Mem0 starts creating memories externally (not via our API), we may need to add logic to create `CompanyBrain`/`UserBrain` records from webhook data.
