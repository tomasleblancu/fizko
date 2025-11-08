# Celery Worker Analysis - Priority Queue Separation

**Date**: 2025-11-07
**Status**: Analysis & Planning Phase
**Risk Level**: Medium (production impact if misconfigured)

## Executive Summary

The current Celery configuration has 3 queues defined (`high`, `default`, `low`) but:
- ❌ **Task routing is NOT working** - routes point to non-existent task names
- ❌ **Single worker processes all tasks** - no queue separation in practice
- ⚠️ **Heavy SII scraping tasks can block critical notifications**

**Recommendation**: Implement 2-worker architecture with corrected routing.

---

## Current State Analysis

### Registered Tasks (Actual Names)

#### Notification Tasks
- `notifications.process_pending` - Process scheduled notifications (every 5 min)
- `notifications.sync_calendar` - Sync calendar notifications (every 15 min)
- `notifications.process_template_notification` - Process template-based notifications

#### Calendar Tasks
- `calendar.sync_company` - Sync calendar for one company
- `calendar.sync_all_companies` - Batch sync for all companies
- `calendar.activate_mandatory_events` - Activate mandatory events
- `calendar.assign_auto_notifications` - Assign auto-notifications

#### SII Tasks (Heavy Selenium Scraping)
- `sii.sync_documents` - Sync tax documents (5-30 min per company)
- `sii.sync_documents_all_companies` - Batch sync all companies
- `sii.sync_f29` - Sync F29 forms
- `sii.sync_f29_all_companies` - Batch sync F29
- `sii.sync_f29_pdfs_missing` - Download missing PDFs
- `sii.sync_f29_pdfs_missing_all_companies` - Batch PDF download

#### Memory Tasks (Mem0 Integration)
- `memory.save_user_memories` - Save user context to Mem0
- `memory.save_company_memories` - Save company context
- `memory.save_onboarding_memories` - Save onboarding data

#### WhatsApp Tasks
- `whatsapp.cleanup_old_sessions` - Clean up old SQLite sessions

### Current Routing Configuration

**File**: `backend/app/infrastructure/celery/config.py`

```python
task_routes = {
    # High priority - Critical operations
    "app.infrastructure.celery.tasks.whatsapp.whatsapp_tasks.*": {"queue": "high"},

    # Default priority - Normal operations
    "app.infrastructure.celery.tasks.documents.document_tasks.*": {"queue": "default"},

    # Low priority - Heavy/slow operations
    "app.infrastructure.celery.tasks.sii.sii_tasks.*": {"queue": "low"},
    "app.infrastructure.celery.tasks.sii.sync_tasks.*": {"queue": "low"},
}
```

**Problem**: These patterns don't match actual task names:
- ❌ `whatsapp.whatsapp_tasks.*` → Actual: `whatsapp.cleanup_old_sessions`
- ❌ `sii.sii_tasks.*` → Actual: `sii.sync_documents`, `sii.sync_f29`, etc.
- ❌ `documents.document_tasks.*` → No such tasks exist

**Result**: ALL tasks currently go to `default` queue (fallback).

---

## Proposed Priority Classification

### 🔴 HIGH Priority Queue
**Criteria**: User-facing, time-sensitive, < 10 seconds execution

- `notifications.process_pending` ⏰ Every 5 min - Users expect timely notifications
- `notifications.sync_calendar` ⏰ Every 15 min - Creates scheduled notifications

**Reasoning**: Notification delays directly impact user experience (F29 reminders, event alerts).

### 🟡 MEDIUM Priority Queue (Default)
**Criteria**: Background operations, tolerate delays, < 5 minutes execution

- `notifications.process_template_notification`
- `calendar.sync_company`
- `calendar.sync_all_companies`
- `calendar.activate_mandatory_events`
- `calendar.assign_auto_notifications`
- `memory.save_user_memories`
- `memory.save_company_memories`
- `memory.save_onboarding_memories`
- `whatsapp.cleanup_old_sessions`

**Reasoning**: Important but not latency-critical. Users don't wait for these.

### 🟢 LOW Priority Queue
**Criteria**: Heavy/long-running, resource-intensive, 5-30+ minutes execution

- `sii.sync_documents` (5-30 min, Selenium scraping)
- `sii.sync_documents_all_companies` (batch, can take hours)
- `sii.sync_f29` (5-15 min)
- `sii.sync_f29_all_companies` (batch)
- `sii.sync_f29_pdfs_missing` (variable)
- `sii.sync_f29_pdfs_missing_all_companies` (batch)

**Reasoning**: These are Selenium-based web scraping tasks that:
- Use significant CPU/memory (Chrome headless)
- Have long execution times
- Can tolerate delays without user impact
- Should NOT block notification processing

---

## Proposed Architecture

### Option A: 2-Worker Setup (RECOMMENDED - Start Here)

**Worker 1: FAST (high + default queues)**
```bash
celery -A app.infrastructure.celery worker \
  -Q high,default \
  --concurrency=3 \
  --loglevel=info \
  --max-tasks-per-child=50 \
  -n fast@%h
```
- Handles all fast tasks (notifications, calendar, memory)
- Concurrency 3 = can handle 3 tasks simultaneously
- `%h` = hostname

**Worker 2: SLOW (low queue only)**
```bash
celery -A app.infrastructure.celery worker \
  -Q low \
  --concurrency=1 \
  --loglevel=info \
  --max-tasks-per-child=10 \
  -n slow@%h
```
- Handles ONLY SII scraping tasks
- Concurrency 1 = one at a time (Selenium is resource-intensive)
- Lower max-tasks-per-child (browser memory leaks)

**Benefits**:
✅ Isolates heavy SII tasks from critical notifications
✅ Simpler than 3 workers
✅ Lower resource overhead
✅ Good for current scale

**Trade-offs**:
⚠️ High and default share resources (but both are fast)

### Option B: 3-Worker Setup (Future Scale)

**Worker 1: HIGH ONLY**
```bash
celery -A app.infrastructure.celery worker -Q high --concurrency=2 -n high@%h
```

**Worker 2: DEFAULT ONLY**
```bash
celery -A app.infrastructure.celery worker -Q default --concurrency=2 -n default@%h
```

**Worker 3: LOW ONLY**
```bash
celery -A app.infrastructure.celery worker -Q low --concurrency=1 -n slow@%h
```

**When to use**: If notification load increases significantly or you need strict SLAs.

---

## Implementation Plan (Incremental & Safe)

### Phase 1: Fix Routing (No Worker Changes Yet) ✅ COMPLETED

**Goal**: Make routing work correctly, but continue using single worker.

**Status**: ✅ **COMPLETED** on 2025-11-07

**Changes Made**:
1. ✅ Updated `backend/app/infrastructure/celery/config.py` with correct task patterns
2. ✅ Created backup: `config.py.backup`
3. ✅ Created verification script: `backend/scripts/verify_celery_routing.py`
4. ✅ Verified all 17 tasks are correctly routed:
   - 2 tasks → `high` queue
   - 9 tasks → `default` queue
   - 6 tasks → `low` queue

**Verification Results**:
```
✅ All user tasks have routing configured
✅ All routing rules point to existing tasks
✅ Routing configuration is complete and valid
```

**Current State**:
- Routing configuration is functional
- Single worker still processes all queues (no operational change yet)
- Tasks will now be distributed to correct queues
- Ready for Phase 2 (multi-worker deployment)

**Rollback**:
```bash
cp backend/app/infrastructure/celery/config.py.backup backend/app/infrastructure/celery/config.py
```

**Testing Completed**:
- ✅ Python syntax validation
- ✅ Configuration loading test
- ✅ Task routing verification (17/17 tasks routed)
- ⏳ Pending: Live testing with running workers

### Phase 2: Add Second Worker (Local Testing) ✅ READY FOR TESTING

**Goal**: Test 2-worker setup in development/staging.

**Status**: ✅ **CONFIGURATION READY** on 2025-11-07

**Changes Made**:
1. ✅ Updated `docker-entrypoint.sh` with queue/worker name support
2. ✅ Created 2-worker `docker-compose.yml` configuration (with profiles)
3. ✅ Created Railway configs: `railway.worker-fast.json`, `railway.worker-slow.json`
4. ✅ Created deployment guide: [CELERY_DEPLOYMENT_GUIDE.md](CELERY_DEPLOYMENT_GUIDE.md)

**Ready to Deploy**:
- **Docker (Local)**: `docker-compose --profile workers up`
- **Railway**: Follow deployment guide to create 2 services

**Testing Steps**:
1. Start Docker with 2 workers: `docker-compose --profile workers up`
2. Verify worker logs show correct queues
3. Check Flower (http://localhost:5555/flower) - should see 2 workers
4. Trigger test tasks and verify routing
5. Monitor for 24-48 hours before Railway deployment

**Rollback**:
```bash
# Docker: Stop profile workers
docker-compose down
docker-compose up  # Back to single worker

# Railway: Pause new workers, re-enable old worker service
```

### Phase 3: Production Deployment (Gradual) ⚠️ MEDIUM-HIGH RISK

**Goal**: Deploy 2-worker setup to production.

**Steps**:
1. Deploy during low-traffic period
2. Start both workers
3. Monitor metrics (queue depths, task latency, errors)
4. Keep single worker config as backup

**Rollback Plan**:
- Stop worker 2 (SLOW)
- Worker 1 (FAST) continues processing `high,default`
- Start single worker that processes all queues
- Stop worker 1

### Phase 4: Monitoring & Optimization 📊

**Metrics to track**:
- Queue depths (high, default, low)
- Task execution time (p50, p95, p99)
- Task failure rate by queue
- Worker CPU/memory usage

**Tools**: Flower (Celery monitoring UI) or Railway metrics.

---

## Risk Assessment

### Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Tasks not routed correctly | High | Medium | Phase 1 testing, gradual rollout |
| Worker crashes | Medium | Low | Supervisor/systemd auto-restart |
| Queue starvation | Medium | Low | Monitor queue depths |
| Deadlocks | Low | Low | Use `task_acks_late=True` (already configured) |
| Memory leaks (Selenium) | Medium | Medium | `max-tasks-per-child=10` for slow worker |

### Current Safety Features (Already in Place)

✅ `task_acks_late = True` - Tasks re-queued if worker crashes
✅ `task_reject_on_worker_lost = True` - Failed tasks are retried
✅ `worker_max_tasks_per_child = 50` - Prevents memory leaks
✅ Database-backed Beat scheduler - Persistent schedules
✅ Retry configuration on all tasks

---

## Proposed Configuration Changes

### File: `backend/app/infrastructure/celery/config.py`

**Replace lines 44-54 with:**

```python
# Task routing - different queues for different priorities
task_routes = {
    # ========== HIGH PRIORITY ==========
    # Critical notifications (time-sensitive, user-facing)
    "notifications.process_pending": {"queue": "high"},
    "notifications.sync_calendar": {"queue": "high"},

    # ========== DEFAULT PRIORITY ==========
    # Background operations (tolerate moderate delays)
    "notifications.process_template_notification": {"queue": "default"},
    "calendar.*": {"queue": "default"},  # All calendar tasks
    "memory.*": {"queue": "default"},    # All memory tasks
    "whatsapp.*": {"queue": "default"},  # WhatsApp tasks

    # ========== LOW PRIORITY ==========
    # Heavy/long-running operations (SII scraping)
    "sii.*": {"queue": "low"},  # All SII tasks
}
```

**Pattern matching**:
- `"task.name"` - Exact match
- `"prefix.*"` - Wildcard match (all tasks starting with prefix)

---

## Next Steps

### Immediate Actions (This Week)
1. ✅ **Review this document** - Validate assumptions
2. ⏳ **Phase 1**: Update routing configuration
3. ⏳ **Testing**: Verify routing in development

### Short-term (Next 2 Weeks)
4. ⏳ **Phase 2**: Test 2-worker setup locally
5. ⏳ **Create deployment scripts** for production
6. ⏳ **Document worker management** (start/stop/monitor)

### Medium-term (Next Month)
7. ⏳ **Phase 3**: Deploy to production (gradual)
8. ⏳ **Phase 4**: Monitor and optimize
9. ⏳ **Consider Phase B** (3 workers) if needed

---

## Questions to Answer Before Proceeding

1. **Current deployment setup**: How are workers currently deployed in production?
   - Railway? Docker? Heroku?
   - How are environment variables managed?
   - How are processes supervised (systemd, Docker, Railway)?

2. **Monitoring**: What monitoring do you have?
   - Flower dashboard?
   - Railway metrics?
   - Custom logging?

3. **Scale**: Current usage patterns?
   - How many companies actively syncing?
   - Notification volume per hour?
   - Average SII sync frequency?

4. **Risk tolerance**:
   - Can we deploy during low-traffic hours?
   - Is there a staging environment?
   - Acceptable downtime window?

---

## Recommendations

### Conservative Approach (RECOMMENDED)
1. Start with **Phase 1 only** (fix routing, single worker)
2. Monitor for 1 week
3. If no issues, proceed to Phase 2 (2 workers in dev)
4. Test thoroughly before production

### Aggressive Approach (Higher Risk)
1. Implement all phases in 2 days
2. Deploy to production immediately
3. Monitor closely

**My recommendation**: **Conservative approach**. The current setup works, so we should:
- Fix routing first (low risk)
- Test thoroughly in dev
- Deploy incrementally to production
- Monitor each step

---

## Open Questions for Discussion

1. ~~Do you want to proceed with Phase 1 (fix routing) now?~~ ✅ **COMPLETED**
2. What is your production deployment environment? (Railway, Docker, etc.)
3. Do you have a staging environment for testing?
4. What monitoring/alerting do you have in place?
5. Any specific concerns or constraints I should know about?

---

## Phase 1 Completion Summary (2025-11-07)

### What Was Changed

**Files Modified**:
- `backend/app/infrastructure/celery/config.py` - Updated task routing configuration
- `backend/CELERY_WORKER_ANALYSIS.md` - Added this analysis document

**Files Created**:
- `backend/app/infrastructure/celery/config.py.backup` - Backup of original config
- `backend/scripts/verify_celery_routing.py` - Routing verification tool

### Routing Configuration Summary

| Queue | Tasks | Purpose |
|-------|-------|---------|
| **high** | 2 tasks | Critical notifications (< 10s execution) |
| **default** | 9 tasks | Background operations (< 5min execution) |
| **low** | 6 tasks | Heavy SII scraping (5-30+ min execution) |

### What Changed Operationally

**Before Phase 1**:
- ❌ All tasks went to `default` queue (routing was broken)
- ⚠️ Heavy SII tasks could block critical notifications

**After Phase 1**:
- ✅ Tasks are correctly routed to appropriate queues
- ✅ Configuration is validated and functional
- ⚠️ **Still using single worker** - no operational impact yet
- ℹ️ To activate queue separation, need to deploy Phase 2 (multiple workers)

### Next Steps

**Immediate** (when ready):
1. Test with single worker to ensure routing doesn't break anything
2. Monitor logs to verify tasks are going to correct queues

**Short-term** (Phase 2 - requires deployment changes):
1. Create worker startup scripts for 2-worker setup
2. Test in development with both workers running
3. Plan production deployment

**To activate multi-worker setup, you'll need to**:
1. Answer the open questions above (deployment environment, etc.)
2. Decide when to proceed with Phase 2
3. Plan deployment strategy (gradual rollout vs. all-at-once)

### Verification Commands

**Check routing configuration**:
```bash
cd backend
.venv/bin/python scripts/verify_celery_routing.py
```

**Test single worker with all queues** (current setup):
```bash
celery -A app.infrastructure.celery worker --loglevel=info
```

**Preview 2-worker setup** (Phase 2 - not deployed yet):
```bash
# Terminal 1 - FAST worker
celery -A app.infrastructure.celery worker -Q high,default --concurrency=3 -n fast@%h

# Terminal 2 - SLOW worker
celery -A app.infrastructure.celery worker -Q low --concurrency=1 -n slow@%h
```
