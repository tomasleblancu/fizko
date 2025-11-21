# Memory Infrastructure (Mem0 Integration)

## Overview

This document describes the memory infrastructure integrated into the backend. The system uses **Mem0** for long-term memory storage with a **Brain pattern** to track memories in Supabase.

**Status**: ✅ Infrastructure Complete (Isolated)
**Date**: November 21, 2024

---

## Architecture

### Components

1. **Database Tables** (`user_brain`, `company_brain`)
   - Track memories stored in Mem0
   - Enable slug-based lookups for updates instead of duplicates
   - PostgreSQL tables with RLS policies

2. **Repositories** ([app/repositories/brain.py](../app/repositories/brain.py))
   - `UserBrainRepository` - Manages user memory records
   - `CompanyBrainRepository` - Manages company memory records
   - Built on Supabase Python client (async)

3. **Memory Service** ([app/services/memory_service.py](../app/services/memory_service.py))
   - `save_company_memories()` - Upsert company memories
   - `save_user_memories()` - Upsert user memories
   - Handles Mem0 API interaction and database sync

4. **Mem0 Client** ([app/integrations/mem0/](../app/integrations/mem0/))
   - Singleton async client
   - Event loop detection for Celery tasks
   - Configurable via `MEM0_API_KEY` environment variable

---

## Database Schema

### Tables

#### `user_brain`

Stores user-specific memories (personal preferences, decisions).

```sql
CREATE TABLE public.user_brain (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    memory_id VARCHAR(255) NOT NULL UNIQUE,  -- Mem0 ID
    slug VARCHAR(255) NOT NULL,              -- Identifier (e.g., "user_full_name")
    content TEXT NOT NULL,                   -- Memory content
    extra_metadata JSONB DEFAULT '{}',       -- Category, etc.
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE(user_id, slug)                    -- Prevent duplicate slugs per user
);
```

#### `company_brain`

Stores company-wide memories (tax regime, policies).

```sql
CREATE TABLE public.company_brain (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    memory_id VARCHAR(255) NOT NULL UNIQUE,  -- Mem0 ID
    slug VARCHAR(255) NOT NULL,              -- Identifier (e.g., "company_tax_regime")
    content TEXT NOT NULL,                   -- Memory content
    extra_metadata JSONB DEFAULT '{}',       -- Category, etc.
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE(company_id, slug)                 -- Prevent duplicate slugs per company
);
```

### RLS Policies

- **User Brain**: Users can only access their own memories (`auth.uid() = user_id`)
- **Company Brain**: Users with active sessions can access company memories

---

## Usage

### 1. Save Company Memories

```python
from app.services import save_company_memories

memories = [
    {
        "slug": "company_tax_regime",
        "category": "company_tax",
        "content": "Régimen tributario: ProPyme General"
    },
    {
        "slug": "company_activity",
        "category": "company_tax",
        "content": "Actividad económica: Comercio al por menor"
    }
]

result = await save_company_memories(company_id="...", memories=memories)
# Returns: {"success": True, "saved_count": 2, "failed_count": 0, "errors": []}
```

### 2. Save User Memories

```python
from app.services import save_user_memories

memories = [
    {
        "slug": "user_full_name",
        "category": "user_profile",
        "content": "Nombre completo: Juan Pérez"
    }
]

result = await save_user_memories(user_id="...", memories=memories)
# Returns: {"success": True, "saved_count": 1, "failed_count": 0, "errors": []}
```

### 3. Repository Access

```python
from app.config.supabase import get_supabase_client
from app.repositories import CompanyBrainRepository

supabase = get_supabase_client()
brain_repo = CompanyBrainRepository(supabase._client)

# Get by slug
memory = await brain_repo.get_by_company_and_slug(
    company_id="...",
    slug="company_tax_regime"
)

# Get all company memories
memories = await brain_repo.get_all_by_company(company_id="...")
```

---

## Memory Pattern

### Slug-Based Updates

Each memory has a unique **slug** that identifies it:
- `"company_tax_regime"` - Company's tax regime
- `"user_full_name"` - User's full name
- `"company_start_date"` - Company start date

When saving a memory:
1. Service checks if slug exists in database
2. If exists → **UPDATE** memory in Mem0 and database
3. If not exists → **CREATE** memory in Mem0 and database

This prevents duplicates and enables organized memory management.

### Memory Synchronization (1:1 Relationship)

**Critical Rule**: Every memory in Mem0 MUST have a corresponding record in the database.

```
Mem0 Memory                    ←→    Database Record
━━━━━━━━━━━━━                      ━━━━━━━━━━━━━━━━━
user_id: "12345678k"              company_id: uuid
memory_id: "mem_abc123"           memory_id: "mem_abc123"
metadata: {                       slug: "company_tax_regime"
  slug: "company_tax_regime",     content: "ProPyme General"
  category: "company_tax"         extra_metadata: {"category": "company_tax"}
}
content: "ProPyme General"
```

The **slug** is the unique identifier:
- Used to find existing memories (for updates)
- Prevents creating duplicate memories
- Must be unique per company/user
- Examples: `"company_tax_regime"`, `"user_full_name"`, `"company_start_date"`

### Entity IDs in Mem0

**IMPORTANT**: Entity IDs in Mem0 use **RUT without hyphens** for both companies and users.

- **Company memories**: Stored with company's **normalized RUT** (e.g., `"12345678k"`)
- **User memories**: Stored with user's **normalized RUT** (e.g., `"98765432k"`)

Example:
```python
# Company with RUT "12.345.678-K"
entity_id = "12345678k"  # Normalized (no dots, no hyphens, lowercase)

# All memories for this company will use "12345678k" as user_id in Mem0
```

This approach:
- ✅ Uses a stable identifier (RUT doesn't change)
- ✅ Avoids UUIDs that can change between environments
- ✅ Makes memories portable across systems
- ✅ Simplifies debugging (RUT is human-readable)

---

## Configuration

### Environment Variables

```bash
# Required for memory system
MEM0_API_KEY=your-mem0-api-key

# Optional: Webhook validation (not implemented yet)
# MEM0_WEBHOOK_SECRET=your-webhook-secret
```

### Check Configuration

```python
from app.integrations.mem0 import is_mem0_configured

if is_mem0_configured():
    print("✅ Mem0 is configured")
else:
    print("⚠️  Mem0 not configured - memory features disabled")
```

---

## Error Handling

The memory service handles:

1. **404 Errors**: Recreates memory if deleted from Mem0
2. **Missing Config**: Gracefully skips if `MEM0_API_KEY` not set
3. **Partial Failures**: Returns success/failure counts per memory

Example response:
```python
{
    "success": False,
    "saved_count": 2,
    "failed_count": 1,
    "errors": [
        "Error with company memory company_invalid: ..."
    ]
}
```

---

## Migration

Apply the migration to create tables:

```bash
# Using Supabase CLI
supabase db push

# Or apply manually
psql $DATABASE_URL < supabase/migrations/20251121195736_create_brain_tables.sql
```

---

## Testing

### Type Check

```bash
python3 -m py_compile app/integrations/mem0/client.py
python3 -m py_compile app/repositories/brain.py
python3 -m py_compile app/services/memory_service.py
```

### Manual Test

```python
import asyncio
from app.services import save_company_memories

async def test():
    memories = [
        {
            "slug": "test_memory",
            "category": "test",
            "content": "This is a test memory"
        }
    ]

    result = await save_company_memories(
        company_id="your-company-id",
        memories=memories
    )

    print(result)

asyncio.run(test())
```

---

## Celery Background Tasks

The memory system includes Celery tasks for loading memories from existing data:

### Available Tasks

#### `memory.load_company_memories`

Load memories for a specific company from existing data:

```python
from app.infrastructure.celery.tasks.memory import load_company_memories

# Load memories for one company
result = load_company_memories.delay("company-uuid-here")
```

**Memories created:**
- `company_tax_regime` - Tax regime (Régimen General, ProPyme, etc.)
- `company_activity` - SII activity name and code
- `company_legal_representative` - Legal representative info
- `company_start_date` - Start of activities date
- `company_accounting_start` - Accounting start month

#### `memory.load_user_memories`

Load memories for a specific user from existing data:

```python
from app.infrastructure.celery.tasks.memory import load_user_memories

# Load memories for one user
result = load_user_memories.delay("user-uuid-here")
```

**Memories created:**
- `user_full_name` - User's full name
- `user_email` - User's email
- `user_phone` - User's phone number
- `user_role` - User's role/position

#### `memory.load_all_companies_memories`

Batch task to load memories for ALL companies:

```python
from app.infrastructure.celery.tasks.memory import load_all_companies_memories

# Load all company memories
result = load_all_companies_memories.delay()
# Returns: {total_companies, loaded_companies, failed_companies, total_memories_created}
```

#### `memory.load_all_users_memories`

Batch task to load memories for ALL users:

```python
from app.infrastructure.celery.tasks.memory import load_all_users_memories

# Load all user memories
result = load_all_users_memories.delay()
# Returns: {total_users, loaded_users, failed_users, total_memories_created}
```

### Running Tasks

**Single company/user:**
```bash
# From Python console
from app.infrastructure.celery.tasks.memory import load_company_memories
load_company_memories.delay("company-id")
```

**Batch processing:**
```bash
# From Python console
from app.infrastructure.celery.tasks.memory import load_all_companies_memories
load_all_companies_memories.delay()
```

---

## What's NOT Included (Yet)

The following features are NOT yet integrated:

- ❌ Agent tools (`search_user_memory`, `save_company_memory`) for AI agents
- ❌ Webhooks for Mem0 events
- ❌ Domain-specific memory modules (onboarding, settings)
- ❌ ChatKit integration

These will be added in subsequent integration steps.

---

## File Structure

```
backend/
├── app/
│   ├── integrations/
│   │   └── mem0/                      # Mem0 integration
│   │       ├── __init__.py            # Export client functions
│   │       └── client.py              # Mem0 async client
│   ├── repositories/
│   │   ├── brain.py                   # Brain repositories
│   │   └── __init__.py                # Export brain repos
│   ├── services/
│   │   ├── memory_service.py          # Memory service layer
│   │   └── __init__.py                # Export memory functions
│   ├── infrastructure/
│   │   └── celery/
│   │       └── tasks/
│   │           ├── memory/            # Memory Celery tasks
│   │           │   ├── __init__.py    # Export memory tasks
│   │           │   └── load.py        # Memory loading tasks
│   │           └── __init__.py        # Task registry (updated)
├── supabase/
│   └── migrations/
│       └── 20251121195736_create_brain_tables.sql  # Database schema
└── docs/
    └── MEMORY_INFRASTRUCTURE.md       # This file
```

---

## Next Steps

To complete the integration:

1. ✅ **Celery Task**: Background tasks to load company/user memories from existing data
2. **Agent Tools**: Create memory tools for AI agents (`search_user_memory`, `save_company_memory`)
3. **Webhooks**: Implement Mem0 webhook handlers for memory events
4. **Domain Modules**: Add onboarding/settings memory builders
5. **Testing**: Add unit tests for repositories and service

### Current Status

✅ **Phase 1: Infrastructure Complete**
- Mem0 integration with RUT-based entity_id
- Brain tables with slug-based upsert
- Memory service with 1:1 synchronization
- Celery tasks for loading memories from existing data

**Phase 2: Agent Integration (Next)**
- Create agent tools to search and save memories
- Integrate with FizkoContext
- Add to specialized agents (supervisor, general knowledge)

**Phase 3: Advanced Features**
- Webhooks for Mem0 events
- Domain-specific memory builders (onboarding flows)
- Memory-aware ChatKit responses

---

## References

- **Old Implementation**: [old-directories/backend/](../../old-directories/backend/)
- **Mem0 Docs**: https://docs.mem0.ai/
- **Original README**: [old-directories/backend/app/agents/tools/memory/README.md](../../old-directories/backend/app/agents/tools/memory/README.md)
