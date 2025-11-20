# Railway Multi-Service Configuration Guide

## Architecture Overview

```
┌─────────────────┐
│   Web Service   │  (FastAPI - port 8000)
│   fizko-web     │
└─────────────────┘
         │
         ├─→ REDIS_URL
         ├─→ DATABASE_URL
         └─→ All env vars

┌─────────────────┐
│ Celery Worker   │  (Background tasks)
│  fizko-worker   │
└─────────────────┘
         │
         ├─→ REDIS_URL (required!)
         ├─→ DATABASE_URL
         └─→ All env vars

┌─────────────────┐
│  Celery Beat    │  (Scheduler)
│   fizko-beat    │
└─────────────────┘
         │
         ├─→ REDIS_URL (required!)
         ├─→ DATABASE_URL (required!)
         └─→ All env vars

┌─────────────────┐
│  Redis Service  │  (Message broker)
│   redis         │
└─────────────────┘
```

## Service Configuration

### 1. Web Service (FastAPI - Already configured)
- **Name**: `fizko-web` or similar
- **Root Directory**: `/backend`
- **Dockerfile Path**: `Dockerfile`
- **Start Command**: `fastapi` (default CMD in Dockerfile)
- **Port**: 8000 (or use $PORT env var)

### 2. Celery Worker Service
- **Name**: `fizko-worker`
- **Root Directory**: `/backend`
- **Dockerfile Path**: `Dockerfile`
- **Start Command Override**: `celery-worker`
- **Environment Variables**:
  ```
  REDIS_URL=${{redis.REDIS_URL}}
  DATABASE_URL=${{Postgres.DATABASE_URL}}
  SUPABASE_URL=${{fizko-web.SUPABASE_URL}}
  SUPABASE_ANON_KEY=${{fizko-web.SUPABASE_ANON_KEY}}
  SUPABASE_JWT_SECRET=${{fizko-web.SUPABASE_JWT_SECRET}}
  OPENAI_API_KEY=${{fizko-web.OPENAI_API_KEY}}
  KAPSO_API_KEY=${{fizko-web.KAPSO_API_KEY}}
  KAPSO_PROJECT_ID=${{fizko-web.KAPSO_PROJECT_ID}}
  ENCRYPTION_KEY=${{fizko-web.ENCRYPTION_KEY}}
  CELERY_CONCURRENCY=2
  CELERY_LOG_LEVEL=info
  ```

### 3. Celery Beat Service
- **Name**: `fizko-beat`
- **Root Directory**: `/backend`
- **Dockerfile Path**: `Dockerfile`
- **Start Command Override**: `celery-beat`
- **Environment Variables**: (Same as worker)
  ```
  REDIS_URL=${{redis.REDIS_URL}}
  DATABASE_URL=${{Postgres.DATABASE_URL}}
  SUPABASE_URL=${{fizko-web.SUPABASE_URL}}
  SUPABASE_ANON_KEY=${{fizko-web.SUPABASE_ANON_KEY}}
  SUPABASE_JWT_SECRET=${{fizko-web.SUPABASE_JWT_SECRET}}
  OPENAI_API_KEY=${{fizko-web.OPENAI_API_KEY}}
  KAPSO_API_KEY=${{fizko-web.KAPSO_API_KEY}}
  KAPSO_PROJECT_ID=${{fizko-web.KAPSO_PROJECT_ID}}
  ENCRYPTION_KEY=${{fizko-web.ENCRYPTION_KEY}}
  CELERY_LOG_LEVEL=info
  ```

### 4. Redis Service
- **Add from Railway Dashboard**:
  1. Click "New Service" → "Database" → "Add Redis"
  2. Railway will automatically create `REDIS_URL` variable
  3. Reference it in other services as `${{redis.REDIS_URL}}`

## Step-by-Step Setup in Railway Dashboard

### Step 1: Add Redis
1. Go to your Railway project
2. Click "+ New Service"
3. Select "Database" → "Add Redis"
4. Wait for deployment (2-3 minutes)
5. Note the service name (usually "redis")

### Step 2: Add Celery Worker
1. Click "+ New Service"
2. Select "GitHub Repo" → Choose your repo
3. Configure service:
   - **Name**: `fizko-worker`
   - **Root Directory**: `backend`
   - **Settings** → **Deploy**:
     - **Custom Start Command**: `celery-worker`
   - **Variables**:
     - Reference Redis: `REDIS_URL=${{redis.REDIS_URL}}`
     - Reference existing DB: `DATABASE_URL=${{Postgres.DATABASE_URL}}`
     - Copy all other env vars from web service
4. Click "Deploy"

### Step 3: Add Celery Beat
1. Click "+ New Service"
2. Select "GitHub Repo" → Choose your repo
3. Configure service:
   - **Name**: `fizko-beat`
   - **Root Directory**: `backend`
   - **Settings** → **Deploy**:
     - **Custom Start Command**: `celery-beat`
   - **Variables**: (Same as worker)
     - `REDIS_URL=${{redis.REDIS_URL}}`
     - `DATABASE_URL=${{Postgres.DATABASE_URL}}`
     - Copy all other env vars
4. Click "Deploy"

## Verification

### Check Service Status
In Railway Dashboard, you should see all 4 services running:
- ✅ `fizko-web` - FastAPI (green, accessible via public domain)
- ✅ `fizko-worker` - Celery Worker (green, no public domain needed)
- ✅ `fizko-beat` - Celery Beat (green, no public domain needed)
- ✅ `redis` - Redis (green, no public domain needed)

### Check Logs

**Celery Worker Logs** should show:
```
celery@... ready.
Connected to redis://...
```

**Celery Beat Logs** should show:
```
DatabaseScheduler: Schedule changed.
Scheduler: Sending due task...
```

**Web Service Logs** should show:
```
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

### Test Background Tasks

From your backend web service or locally:
```python
from app.infrastructure.celery import celery_app

# Send a test task
celery_app.send_task('app.infrastructure.celery.tasks.test_task')
```

Check worker logs to see task execution.

## Troubleshooting

### Worker not processing tasks
- ✅ Check `REDIS_URL` is set correctly
- ✅ Check Redis service is running
- ✅ Check worker logs for connection errors
- ✅ Verify task routing (default queue vs specific queues)

### Beat not scheduling tasks
- ✅ Check `DATABASE_URL` is set (required for database scheduler)
- ✅ Check `REDIS_URL` is set
- ✅ Check beat logs for "Scheduler: Sending due task..."
- ✅ Verify periodic tasks exist in database:
  ```sql
  SELECT * FROM celery_schema.celery_periodictask WHERE enabled = true;
  ```

### Services restarting frequently
- ✅ Check memory limits (Celery with Selenium can use 1-2GB)
- ✅ Check `--max-tasks-per-child=50` setting (worker restarts after 50 tasks)
- ✅ Check for unhandled exceptions in tasks

### Database connection issues
- ✅ Use pgbouncer pooler (port 6543) in `DATABASE_URL`
- ✅ Check connection string format: `postgresql://user:pass@host:6543/db?pgbouncer=true`
- ✅ Verify RLS policies don't block service role access

## Environment Variables Reference

All services need these core variables:

```bash
# Database (Supabase)
DATABASE_URL=postgresql://postgres.[project]:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_ANON_KEY=eyJhbG...
SUPABASE_JWT_SECRET=your-jwt-secret

# Redis (required for Celery)
REDIS_URL=redis://default:[password]@[host]:6379

# OpenAI (for agents)
OPENAI_API_KEY=sk-...

# Kapso (for WhatsApp)
KAPSO_API_KEY=kpk_...
KAPSO_PROJECT_ID=prj_...

# Encryption (for SII credentials)
ENCRYPTION_KEY=your-32-byte-key

# Optional: Celery tuning
CELERY_CONCURRENCY=2
CELERY_LOG_LEVEL=info
```

## Cost Considerations

Railway pricing (as of 2024):
- Each service uses compute time
- Expected usage:
  - Web: 24/7 running (~720 hrs/month)
  - Worker: 24/7 running (~720 hrs/month)
  - Beat: 24/7 running (~720 hrs/month)
  - Redis: 24/7 running (~720 hrs/month)

**Total**: ~2880 compute hours/month + Redis storage

**Tip**: Start with smallest plans, scale up if needed.

## Deployment Workflow

```bash
# 1. Push to GitHub
git add .
git commit -m "Update backend"
git push origin main

# 2. Railway auto-deploys all services
# Watch logs in Railway dashboard

# 3. Verify all services are green
# Check each service's logs

# 4. Test background tasks
# Send a test task, check worker logs
```

## Next Steps

1. ✅ Set up all 4 services in Railway
2. ✅ Configure environment variables
3. ✅ Deploy and verify logs
4. ✅ Test task execution (send a test task)
5. ✅ Set up periodic tasks in database
6. ✅ Monitor service health and resource usage
7. ✅ Consider setting up alerts for service failures

## References

- [Railway Multi-Service Docs](https://docs.railway.app/)
- [Celery Production Checklist](https://docs.celeryproject.org/en/stable/userguide/tasks.html)
- [Docker Entrypoint Script](./backend/docker-entrypoint.sh)
- [Celery Configuration](./backend/app/infrastructure/celery/)
