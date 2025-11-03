# Database Session Management - Best Practices

## Overview

This document explains how database sessions are managed in the Fizko application and provides best practices for different contexts (FastAPI routes, Celery tasks, webhooks, agents).

## TL;DR

- ✅ **FastAPI routes**: Use `Depends(get_db)` - automatic session management
- ✅ **Background tasks/Celery**: Use `get_background_db()` context manager
- ✅ **Webhooks**: Use `get_background_db()` context manager
- ✅ **Agents/Tools**: Pass `db` session from caller, don't create new ones
- ❌ **NEVER**: Create sessions manually with `AsyncSessionLocal()` in application code

---

## Connection Pooling Architecture

### How It Works

The application uses **SQLAlchemy's connection pooling** to efficiently reuse database connections:

```
┌─────────────────┐
│  FastAPI App    │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Engine │  ◄── Created once at startup
    └────┬────┘
         │
    ┌────▼──────────┐
    │ Connection    │  ◄── Pool of 5-15 connections (reused)
    │     Pool      │
    └───────────────┘
         │
    ┌────▼────────┐
    │  Database   │
    └─────────────┘
```

### Pool Configuration

**For direct connections (port 5432)**:
```python
pool_size=5           # 5 permanent connections
max_overflow=10       # up to 15 connections total
pool_recycle=1800     # recycle every 30 minutes
pool_pre_ping=True    # verify connection is alive
```

**For pgbouncer (port 6543)**:
```python
poolclass=NullPool   # Let pgbouncer handle pooling
```

### Key Point

**Connections are reused from the pool**, not created new each time. However, we must avoid creating multiple **Session objects** unnecessarily.

---

## Usage Patterns

### 1. FastAPI Routes (HTTP Endpoints)

**✅ CORRECT** - Use dependency injection:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db

router = APIRouter()

@router.get("/items")
async def list_items(
    company_id: UUID,
    db: AsyncSession = Depends(get_db)  # ✅ Single session for the request
):
    repo = ItemRepository(db)
    items = await repo.find_by_company(company_id)
    return {"data": items}
```

**Benefits:**
- FastAPI automatically manages session lifecycle
- Automatic commit on success, rollback on error
- Connection returned to pool after request

---

### 2. Celery Tasks

**✅ CORRECT** - Use `get_background_db()`:

```python
from app.infrastructure.celery import celery_app
from app.dependencies import get_background_db

@celery_app.task
def sync_data(company_id: str):
    import asyncio

    async def _sync():
        # ✅ Single session for entire task
        async with get_background_db() as db:
            # Find session
            session = await find_active_session(db, company_id)

            # Initialize service with same session
            service = DataService(db)
            result = await service.sync_all(session_id)

            # Commit is automatic
            return result

    return asyncio.run(_sync())
```

**❌ INCORRECT** - Multiple sessions:

```python
@celery_app.task
def sync_data_bad(company_id: str):
    import asyncio
    from app.config.database import AsyncSessionLocal

    async def _find_session():
        # ❌ Session #1
        async with AsyncSessionLocal() as db:
            return await find_active_session(db, company_id)

    async def _sync(session_id):
        # ❌ Session #2 - should reuse session from #1!
        async with AsyncSessionLocal() as db:
            service = DataService(db)
            return await service.sync_all(session_id)

    session_id = asyncio.run(_find_session())  # ❌ Connection used & returned
    return asyncio.run(_sync(session_id))      # ❌ New connection obtained
```

**Why is this bad?**
- Creates 2 Session objects for one logical operation
- Opens and closes connections twice
- Cannot use a single transaction for related operations

---

### 3. Webhooks

**✅ CORRECT** - Use `get_background_db()`:

```python
from fastapi import APIRouter
from app.dependencies import get_background_db

router = APIRouter()

@router.post("/webhook/kapso")
async def handle_kapso_webhook(data: dict):
    async with get_background_db() as db:
        # Process webhook with DB access
        contact = await process_whatsapp_message(db, data)

        # Trigger agent if needed
        if contact.needs_response:
            await run_agent(db, contact)  # ✅ Pass same session

        return {"status": "processed"}
```

---

### 4. AI Agents and Tools

**✅ CORRECT** - Pass session down from caller:

```python
class WhatsAppAgentRunner:
    async def run_agent(self, company_id: UUID, message: str):
        # ✅ Create session once at top level
        async with get_background_db() as db:
            # Load context
            company_info = await load_company_info(db, company_id)

            # Initialize agent with session
            agent = create_unified_agent(db, company_info)

            # Run agent - tools will use the same session
            response = await agent.run(message)

            return response
```

**Agent tools receive the session**:

```python
async def get_tax_documents_tool(
    db: AsyncSession,  # ✅ Passed from agent
    company_id: UUID,
    period: str
):
    repo = TaxDocumentRepository(db)
    documents = await repo.find_by_period(company_id, period)
    return documents
```

---

## Migration Guide

### Identifying Problems

Search for manual session creation:
```bash
grep -r "async with AsyncSessionLocal()" backend/app --include="*.py"
```

### Refactoring Patterns

#### Pattern 1: Consolidate Sequential Sessions

**Before:**
```python
async def _find_session():
    async with AsyncSessionLocal() as db:
        return await db.execute(select(Session.id)...)

async def _process():
    async with AsyncSessionLocal() as db:
        service = MyService(db)
        return await service.do_work()

session_id = asyncio.run(_find_session())  # ❌ Session 1
result = asyncio.run(_process())            # ❌ Session 2
```

**After:**
```python
async def _process():
    async with get_background_db() as db:  # ✅ Single session
        # Find session
        result = await db.execute(select(Session.id)...)
        session_id = result.scalar_one_or_none()

        # Process with same session
        service = MyService(db)
        return await service.do_work(session_id)

result = asyncio.run(_process())
```

#### Pattern 2: Pass Session to Services

**Before:**
```python
class MyService:
    def __init__(self):
        pass

    async def do_work(self):
        async with AsyncSessionLocal() as db:  # ❌ Creates own session
            return await db.execute(...)
```

**After:**
```python
class MyService:
    def __init__(self, db: AsyncSession):
        self.db = db  # ✅ Receives session from caller

    async def do_work(self):
        return await self.db.execute(...)  # ✅ Uses provided session
```

---

## Remaining Work

Files still using `AsyncSessionLocal()` directly:

### To Refactor:
- [ ] `app/routers/whatsapp/main.py` (3 occurrences) - Webhook handlers
- [ ] `app/services/whatsapp/agent_runner.py` - Agent initialization
- [ ] `app/agents/tools/tax/*.py` - Tax tools creating own sessions
- [ ] `app/agents/tools/payroll/*.py` - Payroll tools creating own sessions
- [ ] `app/infrastructure/celery/tasks/calendar/*.py` - Calendar sync tasks
- [ ] `app/infrastructure/celery/tasks/notifications/*.py` - Notification tasks

### Already Refactored:
- [x] `app/infrastructure/celery/tasks/sii/forms.py` - F29 sync tasks
- [x] `app/infrastructure/celery/tasks/sii/documents.py` - Document sync tasks

---

## Performance Benefits

### Before Optimization:
```
Request arrives
  ├── Create Session #1 (get connection from pool)
  ├── Query database
  ├── Close Session #1 (return connection to pool)
  ├── Create Session #2 (get connection from pool)
  ├── Query database
  └── Close Session #2 (return connection to pool)
```

### After Optimization:
```
Request arrives
  ├── Create Session (get connection from pool)
  ├── Query database (multiple queries)
  ├── Query database (reuse same connection)
  └── Close Session (return connection to pool)
```

**Benefits:**
- ✅ Fewer Session objects created
- ✅ Fewer connection checkouts from pool
- ✅ Better transaction boundaries
- ✅ Reduced overhead
- ✅ Clearer code structure

---

## Summary

| Context | Use | Don't Use |
|---------|-----|-----------|
| FastAPI Routes | `Depends(get_db)` | `AsyncSessionLocal()` |
| Celery Tasks | `get_background_db()` | `AsyncSessionLocal()` |
| Webhooks | `get_background_db()` | `AsyncSessionLocal()` |
| Agents/Tools | Pass `db` from caller | Create own session |
| Services | Receive `db` in `__init__` | Create in methods |

**Golden Rule:** Create a session at the **highest level** of your operation, then pass it down to all components that need database access.

---

## Questions?

If unsure about session management in your code:

1. Check if you're in a FastAPI route → Use `Depends(get_db)`
2. Check if you're in a background task/webhook → Use `get_background_db()`
3. Check if you're in a service/tool → Receive `db` from caller
4. Never create multiple sessions for related operations

For examples, see:
- FastAPI routes: `app/routers/tax/form29.py`
- Celery tasks: `app/infrastructure/celery/tasks/sii/forms.py`
- Services: `app/services/sii/service.py`
