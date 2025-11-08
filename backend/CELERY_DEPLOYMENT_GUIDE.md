# Celery Worker Deployment Guide - Multi-Worker Setup

**Last Updated**: 2025-11-07
**Status**: Phase 2 - Ready for Testing

## Overview

This guide explains how to deploy the 2-worker Celery setup (FAST + SLOW) in different environments:
- Docker Compose (local development)
- Railway (staging + production)

## Architecture

### Worker Separation

| Worker | Queues | Concurrency | Purpose | Max Tasks/Child |
|--------|--------|-------------|---------|-----------------|
| **FAST** | high, default | 3 | Notifications, calendar, memory | 100 |
| **SLOW** | low | 1 | SII scraping (Selenium) | 10 |

### Environment Variables

Both workers use these environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `CELERY_QUEUES` | Which queues to process | `high,default` or `low` |
| `CELERY_WORKER_NAME` | Worker identifier | `fast` or `slow` |
| `CELERY_CONCURRENCY` | Number of concurrent tasks | `3` or `1` |
| `CELERY_MAX_TASKS_PER_CHILD` | Restart after N tasks | `100` or `10` |
| `CELERY_LOG_LEVEL` | Logging level | `info` (default) |

---

## Docker Compose Deployment (Local)

### Option 1: Single Worker (Default - Backward Compatible)

**Use case**: Development, testing, or if you don't need worker separation yet.

```bash
# Start all services with single worker
docker-compose up

# Or start specific services
docker-compose up backend celery-worker celery-beat redis
```

**What runs**:
- 1 worker processing ALL queues (high, default, low)
- Concurrency: 2 (default)

### Option 2: Multi-Worker (2 Workers - RECOMMENDED)

**Use case**: Testing Phase 2, simulating production load, full separation.

```bash
# Start all services with 2 workers
docker-compose --profile workers up

# Or in background
docker-compose --profile workers up -d

# View logs
docker-compose --profile workers logs -f celery-worker-fast
docker-compose --profile workers logs -f celery-worker-slow
```

**What runs**:
- **celery-worker-fast**: Processes `high` + `default` queues
  - Concurrency: 3
  - Max tasks/child: 100
- **celery-worker-slow**: Processes `low` queue
  - Concurrency: 1
  - Max tasks/child: 10 (Selenium memory management)

### Switching Between Modes

```bash
# Stop current setup
docker-compose down

# Start with single worker (default)
docker-compose up

# OR start with 2 workers
docker-compose --profile workers up
```

### Monitoring with Flower

```bash
# Flower runs on http://localhost:5555
docker-compose up flower

# Or include with everything
docker-compose --profile workers up
```

Navigate to: http://localhost:5555/flower

You should see:
- `fast@fizko-celery-worker-fast` processing high,default
- `slow@fizko-celery-worker-slow` processing low

---

## Railway Deployment (Staging + Production)

Railway requires separate services for each worker. You'll need to create 2 new services.

### Current Setup (Phase 1 - Single Worker)

**Services**:
1. `backend` - FastAPI
2. `worker` - Celery worker (all queues)
3. `beat` - Celery Beat
4. `flower` - Monitoring (optional)

### New Setup (Phase 2 - Multi-Worker)

**Services**:
1. `backend` - FastAPI (no changes)
2. ~~`worker`~~ - **DELETE** or keep for rollback
3. `worker-fast` - **NEW** - High + Default queues
4. `worker-slow` - **NEW** - Low queue
5. `beat` - Celery Beat (no changes)
6. `flower` - Monitoring (no changes)

### Step-by-Step Railway Deployment

#### Step 1: Create Worker-Fast Service

1. In Railway dashboard, click **"+ New Service"**
2. Select **"Empty Service"**
3. Name it: `worker-fast`
4. Go to **Settings** → **Config** → **Config File**
5. Set config file path: `railway.worker-fast.json`
6. Go to **Variables** and add:

```env
# Shared variables (copy from existing worker)
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Reference from Railway
REDIS_URL=${{Redis.REDIS_URL}}          # Reference from Railway
OPENAI_API_KEY=sk-...                   # Your key
SUPABASE_URL=https://...                # Your Supabase URL
SUPABASE_ANON_KEY=ey...                 # Your Supabase key
KAPSO_API_KEY=...
KAPSO_PROJECT_ID=...
ENCRYPTION_KEY=...

# Worker-specific variables
CELERY_QUEUES=high,default
CELERY_WORKER_NAME=fast
CELERY_CONCURRENCY=3
CELERY_MAX_TASKS_PER_CHILD=100
CELERY_LOG_LEVEL=info
```

7. Save and deploy

#### Step 2: Create Worker-Slow Service

1. Click **"+ New Service"** again
2. Select **"Empty Service"**
3. Name it: `worker-slow`
4. Go to **Settings** → **Config** → **Config File**
5. Set config file path: `railway.worker-slow.json`
6. Go to **Variables** and add:

```env
# Shared variables (same as worker-fast)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=ey...
KAPSO_API_KEY=...
KAPSO_PROJECT_ID=...
ENCRYPTION_KEY=...

# Worker-specific variables
CELERY_QUEUES=low
CELERY_WORKER_NAME=slow
CELERY_CONCURRENCY=1
CELERY_MAX_TASKS_PER_CHILD=10
CELERY_LOG_LEVEL=info
```

7. Save and deploy

#### Step 3: Verify Deployment

1. Check logs for both workers:
   - `worker-fast` should show: `Processing queues: high,default`
   - `worker-slow` should show: `Processing queues: low`

2. Check Flower (if deployed):
   - Navigate to your Flower URL
   - You should see 2 workers:
     - `fast@<hostname>`
     - `slow@<hostname>`

3. Trigger a test task:
   ```python
   # Via FastAPI endpoint or admin panel
   from app.infrastructure.celery.tasks.notifications import process_pending
   process_pending.delay()  # Should go to 'high' queue → worker-fast

   from app.infrastructure.celery.tasks.sii import sync_documents
   sync_documents.delay(session_id="...")  # Should go to 'low' queue → worker-slow
   ```

#### Step 4: Remove Old Worker (Optional)

**WAIT 24-48 hours** to ensure everything works, then:

1. Stop the old `worker` service (don't delete yet)
2. Monitor for 24 hours
3. If no issues, delete the old `worker` service

**Keep it as rollback** if you're cautious.

### Railway Resource Allocation

**Recommendations**:
- `worker-fast`: Medium resources (2 vCPU, 2GB RAM)
- `worker-slow`: Medium resources (2 vCPU, 2GB RAM) - Selenium needs memory
- `beat`: Small resources (0.5 vCPU, 512MB RAM)

### Rollback Strategy (Railway)

If issues arise:

1. **Quick rollback**: Re-enable old `worker` service
2. **Stop new workers**: Pause `worker-fast` and `worker-slow`
3. **Old worker resumes** processing all queues
4. **Investigate issues** in logs
5. **Try again** after fixing

---

## Testing & Verification

### Local Testing (Docker)

```bash
# 1. Start with 2 workers
docker-compose --profile workers up

# 2. In another terminal, trigger test tasks
docker-compose exec backend bash

# Inside container:
python
>>> from app.infrastructure.celery.tasks.notifications import process_pending
>>> from app.infrastructure.celery.tasks.sii import sync_documents
>>>
>>> # Trigger high-priority task
>>> result = process_pending.delay()
>>> print(f"Task ID: {result.id}")
>>>
>>> # Trigger low-priority task (requires session_id)
>>> # result = sync_documents.delay(session_id="your-session-id")

# 3. Check Flower
# Open http://localhost:5555/flower
# Verify tasks are routed correctly:
#   - process_pending → worker-fast (high queue)
#   - sync_documents → worker-slow (low queue)
```

### Production Verification (Railway)

1. **Check worker logs**:
   ```
   worker-fast logs should show:
   🔨 Starting Celery Worker
   ℹ  Processing queues: high,default
   ℹ  Worker name: fast

   worker-slow logs should show:
   🔨 Starting Celery Worker
   ℹ  Processing queues: low
   ℹ  Worker name: slow
   ```

2. **Monitor Flower**:
   - Both workers online
   - Tasks routing correctly
   - No task failures

3. **Test actual workflows**:
   - Trigger a notification (should be fast)
   - Trigger SII sync (should go to slow worker)
   - Verify no blocking

---

## Monitoring & Alerting

### Key Metrics to Watch

| Metric | Tool | What to Monitor |
|--------|------|-----------------|
| **Queue depth** | Flower | Should stay low (< 10 pending) |
| **Task success rate** | Flower | Should be > 95% |
| **Worker CPU** | Railway/Docker Stats | worker-slow should be high during SII sync |
| **Worker Memory** | Railway/Docker Stats | Watch for memory leaks |
| **Task execution time** | Flower | High queue: < 10s, Default: < 5min, Low: variable |

### Flower Commands

```bash
# Local (Docker)
http://localhost:5555/flower

# Railway
https://your-flower-app.railway.app/flower
```

**Key views**:
- `/flower/workers` - Worker status, queues, concurrency
- `/flower/tasks` - Task history, success/failure rates
- `/flower/monitor` - Real-time task monitoring

---

## Troubleshooting

### Issue: Tasks Not Being Processed

**Symptom**: Tasks stay in queue, not picked up.

**Check**:
1. Are workers running?
   ```bash
   # Docker
   docker-compose ps

   # Railway
   Check service status in dashboard
   ```

2. Are queues configured correctly?
   ```bash
   # Check worker logs for "Processing queues: ..."
   docker-compose logs celery-worker-fast | grep "Processing queues"
   ```

3. Is Redis accessible?
   ```bash
   # Test Redis connection
   docker-compose exec backend python -c "import redis; r = redis.from_url('redis://redis:6379'); print(r.ping())"
   ```

### Issue: Worker Keeps Restarting

**Symptom**: Worker crashes and restarts frequently.

**Possible causes**:
1. **Memory leak** (Selenium): Check `max-tasks-per-child`
2. **Task timeout**: Increase `task_soft_time_limit` in config
3. **Database connection**: Check DATABASE_URL

**Solution**:
```bash
# Reduce max-tasks-per-child for slow worker
CELERY_MAX_TASKS_PER_CHILD=5  # Instead of 10
```

### Issue: High Queue Tasks Not Prioritized

**Symptom**: Notifications delayed even with worker-fast.

**Check**:
1. Routing configuration:
   ```bash
   cd backend
   .venv/bin/python scripts/verify_celery_routing.py
   ```

2. Worker-fast is running:
   ```bash
   docker-compose ps | grep worker-fast
   ```

3. High queue has tasks:
   ```bash
   # In Flower, check queue depths
   ```

---

## Commands Reference

### Docker Compose

```bash
# Single worker (default)
docker-compose up

# Multi-worker (2 workers)
docker-compose --profile workers up

# Stop everything
docker-compose down

# View logs
docker-compose logs -f celery-worker-fast
docker-compose logs -f celery-worker-slow

# Restart specific worker
docker-compose restart celery-worker-fast

# Shell into container
docker-compose exec celery-worker-fast bash
```

### Celery CLI (Inside Container/Railway)

```bash
# List active queues
celery -A app.infrastructure.celery inspect active_queues

# View registered tasks
celery -A app.infrastructure.celery inspect registered

# Purge queue (CAREFUL - deletes all pending tasks)
celery -A app.infrastructure.celery purge -Q low

# Check worker stats
celery -A app.infrastructure.celery inspect stats
```

---

## Next Steps

### Phase 2 Checklist

- [ ] Test multi-worker locally with Docker Compose
- [ ] Verify routing with `verify_celery_routing.py`
- [ ] Deploy to Railway staging
- [ ] Monitor for 24 hours
- [ ] Deploy to Railway production
- [ ] Monitor for 48 hours
- [ ] Remove old worker service (optional)

### Phase 3: Monitoring & Optimization

- [ ] Set up Flower with authentication
- [ ] Configure alerts (Railway notifications, PagerDuty, etc.)
- [ ] Fine-tune concurrency based on load
- [ ] Consider 3-worker setup if needed (high, default, low)

---

## Questions?

- **Phase 1 docs**: [CELERY_WORKER_ANALYSIS.md](CELERY_WORKER_ANALYSIS.md)
- **Routing verification**: `python scripts/verify_celery_routing.py`
- **Celery docs**: https://docs.celeryq.dev/

**Need help?** Check logs, Flower dashboard, and Railway metrics.
