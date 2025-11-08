# Fix: Mem0 Client Premature Closure in Celery Tasks

## Problem

Celery tasks for saving memories were failing with error:
```
RuntimeError: Cannot send a request, as the client has been closed.
```

### Root Cause

The Mem0 async client was being explicitly closed in the `finally` block of Celery tasks **before** all async operations completed:

```python
finally:
    if mem0 is not None:
        await mem0.async_client.aclose()  # ❌ Closes client prematurely
```

Since `get_mem0_client()` returns a **singleton** global instance, closing it in one task affects all pending operations. The HTTP client inside Mem0 was being closed while operations were still in flight.

## Solution

**Removed explicit client closure** from Celery tasks. The singleton pattern handles lifecycle management automatically.

### Files Fixed

1. **[backend/app/infrastructure/celery/tasks/memory/company.py](app/infrastructure/celery/tasks/memory/company.py)**
   - Removed `finally` block that closed `mem0.async_client`
   - Let singleton manage client lifecycle

2. **[backend/app/infrastructure/celery/tasks/memory/user.py](app/infrastructure/celery/tasks/memory/user.py)**
   - Removed `finally` block that closed `mem0.async_client`
   - Let singleton manage client lifecycle

### Before (Broken)

```python
async def _save():
    mem0 = None
    try:
        async with AsyncSessionLocal() as db:
            mem0 = get_mem0_client()
            # ... save operations ...
    except Exception as e:
        # ... error handling ...
    finally:
        # ❌ THIS BREAKS - Closes client while operations pending
        if mem0 is not None:
            await mem0.async_client.aclose()
```

### After (Fixed)

```python
async def _save():
    try:
        async with AsyncSessionLocal() as db:
            mem0 = get_mem0_client()  # ✅ Singleton manages lifecycle
            # ... save operations ...
    except Exception as e:
        # ... error handling ...
    # ✅ No explicit close - singleton handles it
```

## Why This Works

1. **Singleton Pattern**: `get_mem0_client()` returns the same instance across all calls
2. **Shared State**: In multiprocessing (Celery fork mode), each worker has its own copy
3. **Automatic Cleanup**: httpx/AsyncMemoryClient handle cleanup when process ends
4. **No Race Conditions**: Removing explicit close prevents premature shutdown

## Testing

After deploying this fix:

1. **Call subscription endpoint** to trigger memory sync:
   ```bash
   curl http://localhost:8089/api/subscriptions/current
   ```

2. **Check Celery logs** for success (should see no "client has been closed" errors):
   ```
   [Memory Task] 🧠 Starting company memory save for {company_id} (3 memories)
   [Memory Service] ✨ Creating company memory: company_subscription_plan
   [Memory Service] ✅ Created company memory: company_subscription_plan
   [Memory Service] ✨ Creating company memory: company_subscription_features
   [Memory Service] ✅ Created company memory: company_subscription_features
   [Memory Service] ✨ Creating company memory: company_subscription_trial
   [Memory Service] ✅ Created company memory: company_subscription_trial
   [Memory Task] ✅ Company memory save completed for {company_id}
   ```

3. **Verify in database** that memories were created:
   ```sql
   SELECT slug, content FROM company_brain
   WHERE company_id = '{company_id}'
   AND slug LIKE 'company_subscription_%';
   ```

## Deployment

### Production (Railway)

Push changes to `main` branch:
```bash
git add backend/app/infrastructure/celery/tasks/memory/
git commit -m "fix: remove premature Mem0 client closure in Celery tasks"
git push origin main
```

Railway will automatically:
1. Rebuild backend container
2. Restart Celery workers with new code
3. Apply fix immediately

### Local Testing

If running Celery locally:
```bash
# Kill existing workers
pkill -f "celery.*worker"

# Start fresh worker
cd backend
.venv/bin/celery -A app.infrastructure.celery worker --loglevel=info
```

## Impact

- ✅ Fixes subscription memory sync
- ✅ Fixes all company memory saves (SII auth, settings)
- ✅ Fixes all user memory saves (preferences, onboarding)
- ✅ No breaking changes - only removes problematic code

## Related Issues

This same pattern affects any Celery task using the Mem0 singleton client. The fix ensures:
- Onboarding memories work correctly
- SII auth memories work correctly
- Settings memories work correctly
- **NEW: Subscription memories work correctly**

## References

- Mem0 async client docs: https://docs.mem0.ai/
- Python singleton pattern: https://refactoring.guru/design-patterns/singleton/python/example
- httpx async client lifecycle: https://www.python-httpx.org/advanced/#client-instances
