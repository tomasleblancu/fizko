# Mem0 404 Orphan Memory Fix

## Problem

When attempting to update subscription memories in Mem0, the system was failing with 404 errors:

```
[Memory Service] ❌ Error with company memory company_subscription_plan:
Client error '404 Not Found' for url 'https://api.mem0.ai/v1/memories/2e982c88-...'
```

### Root Cause

1. **Manual Cleanup**: Subscriptions were manually deleted from database
2. **Memory Deletion**: Memories were deleted from `company_brain` table
3. **New Memory Creation**: System created new records in `company_brain` with new memory_ids
4. **Orphaned Memories**: Old memories still existed in Mem0
5. **Stale References**: Database had memory_ids that no longer existed in Mem0

### Error Flow

```
Subscription endpoint called
  ↓
save_subscription_memories() dispatched via Celery
  ↓
memory_service._save_memories()
  ↓
Finds existing_brain record in DB
  ↓
Attempts mem0_client.update(memory_id=existing_brain.memory_id, ...)
  ↓
ERROR: 404 Not Found - memory doesn't exist in Mem0 ❌
```

### User Impact

- AI agent was seeing stale subscription data ("Plan Básico" instead of "Free")
- Memory updates were failing silently in background tasks
- Celery tasks were being marked as failed

## Solution

Modified `memory_service._save_memories()` to detect 404 errors and gracefully recover by recreating the memory.

### File: `backend/app/services/memory_service.py`

**Added error handling around memory update (lines 143-206):**

```python
if existing_brain:
    # Try UPDATE en Mem0
    logger.info(
        f"[Memory Service] 🔄 Updating {entity_type} memory: {slug} "
        f"(category: {category})"
    )

    try:
        await mem0_client.update(
            memory_id=existing_brain.memory_id,
            text=content
        )

        # Actualizar en BD usando repositorio
        await brain_repo.update(
            id=existing_brain.id,
            content=content,
            extra_metadata={"category": category}
        )
        logger.info(
            f"[Memory Service] ✅ Updated {entity_type} memory: {slug}"
        )

    except Exception as update_error:
        # Check if memory doesn't exist in Mem0 (404)
        error_str = str(update_error).lower()
        is_not_found = "404" in error_str or "not found" in error_str

        if is_not_found:
            logger.warning(
                f"[Memory Service] ⚠️  Memory {slug} not found in Mem0, "
                f"recreating..."
            )

            # CREATE new memory in Mem0
            result = await mem0_client.add(
                messages=[{"role": "user", "content": content}],
                user_id=entity_id,
                metadata={"slug": slug, "category": category}
            )

            # Extract new memory_id
            new_memory_id = _extract_memory_id(result)

            if new_memory_id:
                # Update DB with new memory_id
                await brain_repo.update(
                    id=existing_brain.id,
                    memory_id=new_memory_id,
                    content=content,
                    extra_metadata={"category": category}
                )
                logger.info(
                    f"[Memory Service] ✅ Recreated {entity_type} memory: "
                    f"{slug} (new ID: {new_memory_id})"
                )
            else:
                logger.error(
                    f"[Memory Service] ❌ Failed to get memory_id after "
                    f"recreating {slug}"
                )
        else:
            # Other error, re-raise
            raise
```

### Key Changes

1. **Try-Catch Around Update**: Wrap `mem0_client.update()` in try-except
2. **Detect 404 Errors**: Check if error message contains "404" or "not found"
3. **Recreate Memory**: Call `mem0_client.add()` to create new memory in Mem0
4. **Update Database**: Store new memory_id in `company_brain` table
5. **Preserve Data**: Content and metadata remain unchanged
6. **Graceful Logging**: Log warning when recreating, success when done

## How It Works

### Before Fix (Fails)

```
Celery Task: save_subscription_memories
  ├─ Find existing_brain record (memory_id: old_123)
  ├─ Try mem0_client.update(memory_id=old_123, ...)
  ├─ ERROR: 404 Not Found ❌
  └─ Task fails, memory not updated
```

### After Fix (Recovers)

```
Celery Task: save_subscription_memories
  ├─ Find existing_brain record (memory_id: old_123)
  ├─ Try mem0_client.update(memory_id=old_123, ...)
  ├─ Detect 404 error
  ├─ ⚠️  Log: "Memory not found in Mem0, recreating..."
  ├─ Create new memory in Mem0 → new_memory_id: new_456
  ├─ Update company_brain.memory_id = new_456
  ├─ Update company_brain.content = new content
  └─ ✅ Success - memory recreated and synced
```

## Testing

### Expected Log Output (Success)

```
[Memory Service] 🔄 Updating company memory: company_subscription_plan
[Memory Service] ⚠️  Memory company_subscription_plan not found in Mem0, recreating...
[Memory Service] Mem0 status: COMPLETED, memory_id: mem_abc123xyz
[Memory Service] ✅ Recreated company memory: company_subscription_plan (new ID: mem_abc123xyz)
```

### Verification Steps

1. **Check Database**: Verify `company_brain` has new memory_id
   ```sql
   SELECT memory_id, content, updated_at
   FROM company_brain
   WHERE slug = 'company_subscription_plan'
   AND company_id = '628771e2-6912-4e7f-8bb9-ff69f7d334e3';
   ```

2. **Check Mem0**: Query Mem0 API to verify memory exists
   ```python
   mem0_memories = await mem0.get_all(user_id=f"company_{company_id}")
   # Should find memory with new ID
   ```

3. **Test AI Agent**: Ask agent about subscription, should respond with correct plan

## Benefits

1. **Self-Healing**: System automatically recovers from orphaned memory references
2. **No Data Loss**: Content is recreated in Mem0 from database
3. **Backward Compatible**: Works with existing memories, no migration needed
4. **Transparent**: Logs clearly show when recreation occurs
5. **Zero Downtime**: No manual intervention required

## Related Issues

This fix complements previous memory system improvements:

1. **Subscription Optimization** ([SUBSCRIPTION_MEMORY_OPTIMIZATION.md](SUBSCRIPTION_MEMORY_OPTIMIZATION.md))
   - Only saves memory when subscription changes
   - Reduces unnecessary memory operations

2. **Event Loop Fix** ([MEM0_EVENT_LOOP_FIX.md](MEM0_EVENT_LOOP_FIX.md))
   - Detects event loop changes in Celery tasks
   - Prevents "Event loop is closed" errors

All three fixes work together to create a robust memory system:
- **Optimization**: Reduces unnecessary saves (efficiency)
- **Event Loop**: Prevents client errors (reliability)
- **404 Recovery**: Handles orphaned memories (resilience)

## Edge Cases Handled

1. **404 on Update**: Recreates memory with new ID ✅
2. **Missing memory_id in Response**: Logs error but doesn't crash ✅
3. **Other Exceptions**: Re-raises for proper error handling ✅
4. **Company vs User Memories**: Works for both entity types ✅
5. **Multiple Slugs**: Each memory handled independently ✅

## Prevention

To avoid orphaned memories in the future:

1. **Don't Manually Delete**: Avoid manually deleting from `company_brain` without deleting from Mem0
2. **Use Service Layer**: Always use `memory_service` functions for memory operations
3. **Delete Properly**: If cleanup needed, delete from both Mem0 and database:
   ```python
   # Delete from Mem0 first
   await mem0.delete(memory_id=brain.memory_id)
   # Then delete from DB
   await db.delete(brain)
   ```

## Deployment Notes

- ✅ No database migrations needed
- ✅ No environment variable changes
- ✅ Backward compatible with existing memories
- ✅ Celery workers will pick up change on restart
- ✅ No API contract changes

## Monitoring

After deployment, monitor:

1. **Celery Logs**: Watch for "recreating..." warnings
2. **Memory Consistency**: Compare `company_brain` memory_ids with Mem0
3. **Agent Responses**: Verify agents use correct subscription data
4. **Error Rates**: 404 errors should disappear after first recreate

## Files Modified

- [backend/app/services/memory_service.py](app/services/memory_service.py) - Added 404 error handling

## Cleanup Script

Optional: Run cleanup script to identify and fix orphaned memories proactively:

```bash
cd backend
source .env
python clean_mem0_orphans.py
```

This script:
- Finds memories in Mem0 not in database
- Finds memories in database not in Mem0
- Offers to clean up inconsistencies

**Note**: With the 404 fix deployed, cleanup happens automatically, so this script is optional.
