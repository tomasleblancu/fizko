# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fizko is a tax and accounting platform for small businesses in Chile. The system combines:
- **Multi-agent AI system** for tax consultation (based on OpenAI ChatKit)
- **SII integration** for automated tax document extraction via Selenium scraping
- **WhatsApp integration** via Kapso for conversational assistance
- **Celery + Redis** for background tasks and scheduled notifications
- **PostgreSQL** (Supabase) for data persistence with RLS

## Development Commands

### Backend (FastAPI + Python 3.11+)

```bash
cd backend

# Install dependencies (uses uv package manager)
uv sync

# Development server (PRODUCTION PARITY - recommended)
./dev.sh
# Runs Gunicorn + 2 Uvicorn workers on port 8089
# Uses pgbouncer pooler (port 6543) for production-like DB connection

# Alternative: Quick dev server (NOT production-like)
uv run uvicorn app.main:app --reload --port 8089

# Run Celery worker
.venv/bin/celery -A app.infrastructure.celery worker --loglevel=info

# Run Celery Beat scheduler
./start_beat.sh
# Or manually:
.venv/bin/celery -A app.infrastructure.celery beat --loglevel=info

# Run single test file
.venv/bin/pytest tests/path/to/test_file.py -v

# Type checking
python3 -m py_compile app/**/*.py

# Format code
uv run ruff format .

# Lint
uv run ruff check .
```

**Important**: Always use `./dev.sh` for local development to match production configuration (Gunicorn + pgbouncer pooler on port 6543).

### Frontend (React 19 + TypeScript + Vite 7)

```bash
cd frontend

# Install dependencies
npm install

# Development server (port 5171)
npm run dev

# Type check
npm run type-check
# Or:
npx tsc --noEmit

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

### Database Migrations

Migrations are in `backend/supabase/migrations/`. Apply manually to Supabase using the SQL editor or Supabase CLI.

### Seed Scripts (Data Sync Between Environments)

Sync configuration data between environments using Supabase SDK:

```bash
cd backend

# Sync notification templates from staging to production
python -m scripts.seed notification-templates --to production --dry-run
python -m scripts.seed notification-templates --to production

# Sync event templates
python -m scripts.seed event-templates --to production --dry-run
python -m scripts.seed event-templates --to production

# Sync specific templates only
python -m scripts.seed notification-templates --to production --codes f29_reminder,daily_summary

# Sync any table generically (new brain system, etc.)
python -m scripts.seed sync --table brain_contexts --unique-key context_id --to production --dry-run

# Sync everything
python -m scripts.seed all --to production --dry-run
python -m scripts.seed all --to production
```

**Required environment variables** for seed scripts:
- `STAGING_SUPABASE_URL`, `STAGING_SUPABASE_SERVICE_KEY` - Staging environment
- `PROD_SUPABASE_URL`, `PROD_SUPABASE_SERVICE_KEY` - Production environment

See [backend/scripts/seed/README.md](backend/scripts/seed/README.md) and [QUICKSTART.md](backend/scripts/seed/QUICKSTART.md) for full documentation.

### Environment Setup

**Backend** requires `.env` file with:
- `OPENAI_API_KEY` - For AI agents
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET` - Database & auth (local/staging/prod)
- `DATABASE_URL` - PostgreSQL connection (use port **6543** for pgbouncer pooler in production parity)
- `KAPSO_API_KEY`, `KAPSO_PROJECT_ID` - WhatsApp integration
- `REDIS_URL` - For Celery (format: `redis://host:port/db` or `redis://:password@host:port/db`)
- `ENCRYPTION_KEY` - For encrypting SII credentials

**For seed scripts** (data sync between environments):
- `STAGING_SUPABASE_URL`, `STAGING_SUPABASE_SERVICE_KEY` - Staging Supabase credentials
- `PROD_SUPABASE_URL`, `PROD_SUPABASE_SERVICE_KEY` - Production Supabase credentials

**Frontend** requires `.env` file with:
- `VITE_BACKEND_URL` - Backend API URL (default: `http://localhost:8089`)
- `VITE_CHATKIT_API_DOMAIN_KEY` - ChatKit domain key
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` - For auth

See `.env.example` files in each directory.

## Architecture

### Multi-Agent System

The backend uses a **supervisor + specialized agents** architecture:

```
User Query
    ↓
POST /chatkit
    ↓
HandoffsManager.get_supervisor_agent()
    ↓
Supervisor Agent (routes to specialists)
    ↓
├─→ General Knowledge Agent (general questions)
├─→ Tax Documents Agent (DTEs, invoicing)
└─→ [Other specialized agents]
```

**Key files:**
- [backend/app/agents/orchestration/handoffs_manager.py](backend/app/agents/orchestration/handoffs_manager.py) - Singleton manager that caches orchestrators per thread
- [backend/app/agents/specialized/supervisor_agent.py](backend/app/agents/specialized/supervisor_agent.py) - Entry point agent that routes queries
- [backend/app/agents/specialized/](backend/app/agents/specialized/) - Specialized agents
- [backend/app/agents/tools/](backend/app/agents/tools/) - Agent tools organized by domain (tax/, widgets/)

**Important conventions:**
- All agents use `FizkoContext` for shared state (company info, user data)
- Company information is auto-loaded at conversation start (no tool call needed)
- Agents support two channels: `chatkit` (with UI widgets) and `whatsapp` (text-only)
- Use absolute imports: `from app.agents...`
- All database operations are async with SQLAlchemy 2.0

### Backend Structure

```
backend/app/
├── agents/              # Multi-agent AI system
│   ├── core/           # FizkoContext, context loaders, attachment stores
│   ├── orchestration/  # HandoffsManager, multi-agent orchestrator
│   ├── specialized/    # Specialized agents (supervisor, general_knowledge, tax_documents)
│   ├── tools/          # Agent tools (tax/, widgets/)
│   └── ui_tools/       # UI tool system (notifications, interactive components)
├── routers/            # FastAPI route handlers
│   ├── admin/         # Admin routes (companies, calendar, notifications, templates)
│   ├── auth/          # Authentication (profile)
│   ├── chat/          # ChatKit integration
│   ├── companies/     # Company management
│   ├── personnel/     # Payroll and people management
│   ├── scheduled_tasks/ # Celery Beat task management
│   ├── sii/           # SII integration (auth, sync)
│   ├── tax/           # Tax endpoints (documents, F29, purchases, sales, summary)
│   └── whatsapp/      # WhatsApp integration (modular: routes/, handlers/)
├── services/          # Business logic layer
│   ├── agents/        # Agent service layer
│   ├── calendar/      # Calendar event management
│   ├── notifications/ # Notification system (modular: modules/)
│   ├── scheduled_tasks/ # Beat and scheduler services
│   ├── sii/           # SII service layer (auth, document, form, sync)
│   └── whatsapp/      # WhatsApp services (agent_runner, conversation_manager, media_processor)
├── integrations/      # External service clients
│   ├── kapso/         # Kapso WhatsApp API client
│   └── sii/           # SII RPA (Selenium scraping)
│       ├── client/    # SIIClient unified API
│       ├── scrapers/  # Web scrapers (F29, DTEs, boletas honorario)
│       └── extractors/ # Data extractors
├── infrastructure/    # Infrastructure layer
│   └── celery/        # Celery app + tasks
│       └── tasks/     # Task modules (sii/, calendar/, notifications/)
├── db/               # Database layer
│   └── models/       # SQLAlchemy models
├── config/           # Configuration
│   ├── constants.py  # Model names, agent instructions
│   └── database.py   # SQLAlchemy async engine
├── dependencies/     # FastAPI dependencies
├── repositories/     # Data access layer (if used)
└── main.py          # FastAPI application entry point
```

### Frontend Structure (Feature-Sliced Design)

```
frontend/src/
├── app/              # Application layer
│   ├── main.tsx     # Entry point
│   ├── providers/   # Context providers (Auth, React Query)
│   └── styles/      # Global styles
├── features/         # Feature modules
│   ├── admin/       # Admin features (companies, notifications, tasks)
│   ├── contacts/    # Contact management
│   ├── dashboard/   # Financial dashboard
│   ├── payroll/     # Payroll management
│   └── profile/     # User profile
├── pages/           # Page components
│   ├── home/       # Home page and landing
│   └── legal/      # Legal pages
├── widgets/         # Complex UI widgets
│   ├── chat-panel/ # ChatKit integration
│   └── navbar/     # Navigation
└── shared/          # Shared utilities
    ├── components/  # Reusable components
    ├── hooks/      # Custom React hooks (useSession, useCompanyQuery, etc.)
    ├── lib/        # Libraries (supabase, query-keys)
    ├── types/      # TypeScript types
    └── ui/         # UI primitives (feedback, etc.)
```

**Important patterns:**
- Use `useSession()` hook for auth state (NOT deprecated `useUserProfile()`)
- Use React Query (`@tanstack/react-query`) for all server state
- Centralize query keys in `shared/lib/query-keys.ts`
- File references in code should use format: `[filename.ts:42](src/filename.ts#L42)` for clickability

### SII Integration (Selenium RPA)

The SII integration uses Selenium to scrape the Chilean tax authority portal:

**Architecture:**
- [backend/app/integrations/sii/client/](backend/app/integrations/sii/client/) - Unified `SIIClient` class
- [backend/app/integrations/sii/scrapers/](backend/app/integrations/sii/scrapers/) - Web scrapers for different data types
- [backend/app/integrations/sii/extractors/](backend/app/integrations/sii/extractors/) - Data extraction logic

**Key capabilities:**
- Automatic authentication with session persistence (cookie reuse)
- DTE extraction (compras/ventas) via SII API with authenticated cookies
- F29 form extraction and parsing
- Boletas honorarios (receipts) scraping
- Contributor information extraction

**Usage pattern:**
```python
from app.integrations.sii import SIIClient

async with SIIClient(rut=rut, password=password, db=db, company_id=company_id) as client:
    await client.login()
    compras = await client.get_compras(periodo="202501")
    ventas = await client.get_ventas(periodo="202501")
```

### WhatsApp Integration

WhatsApp integration via Kapso uses a modular router structure:

**Routes:** [backend/app/routers/whatsapp/routes/](backend/app/routers/whatsapp/routes/)
- `messaging.py` - Send text, media, templates, interactive messages
- `conversations.py` - Conversation CRUD
- `contacts.py` - Contact search, message history
- `webhooks.py` - Webhook processing (HMAC validation, media processing, AI agent execution)
- `misc.py` - Templates, inbox, health check

**Services:** [backend/app/services/whatsapp/](backend/app/services/whatsapp/)
- `service.py` - Main WhatsApp service
- `agent_runner.py` - Executes AI agents for WhatsApp messages
- `conversation_manager.py` - Manages conversation state
- `media_processor.py` - Processes images and PDFs from WhatsApp

**Key flow for webhooks:**
1. Validate HMAC signature
2. Parse events (supports batching)
3. Authenticate user by WhatsApp phone number
4. Detect notification context (if replying to a notification)
5. Process media (images, PDFs via OCR/parsing)
6. Execute AI agent with context
7. Send response via Kapso
8. Save conversation history in background

### Celery Background Tasks

**Celery app:** [backend/app/infrastructure/celery/](backend/app/infrastructure/celery/)
**Tasks:** [backend/app/infrastructure/celery/tasks/](backend/app/infrastructure/celery/tasks/)

Key task categories:
- `sii/` - SII document and form syncing
- `calendar/` - Calendar event processing
- `notifications/` - Notification scheduling and delivery

**Important:**
- Redis URL format: `redis://host:port/db` or `redis://:password@host:port/db`
- Use `./start_beat.sh` for Celery Beat scheduler
- Celery worker: `.venv/bin/celery -A app.infrastructure.celery worker --loglevel=info`

### Notification System

Modular notification system in [backend/app/services/notifications/](backend/app/services/notifications/):

**Usage:**
```python
from app.services.notifications import send_instant_notification

await send_instant_notification(
    db,
    company_id,
    ["+56912345678"],
    "Your F29 was processed successfully!"
)
```

**Key features:**
- Template-based notifications with variable substitution
- Calendar event reminders (7d, 3d, 1d, today)
- F29 due date reminders
- Scheduled delivery with Celery
- WhatsApp integration via Kapso
- Notification history tracking

### Service Layer Pattern

The codebase follows a **service layer pattern** for separation of concerns:

```
HTTP Router (FastAPI)
    ↓ delegates to
Service Layer (business logic)
    ↓ uses
Models & Database (SQLAlchemy)
```

**Benefits:**
- Testability: Services can be tested without HTTP layer
- Reusability: Services used by routers, CLI, Celery tasks
- Single responsibility: Routers handle HTTP, services handle logic
- Maintainability: Changes to logic don't affect HTTP layer

**Examples:**
- [backend/app/services/scheduled_tasks/](backend/app/services/scheduled_tasks/) - `BeatService` and `SchedulerService`
- [backend/app/services/sii/](backend/app/services/sii/) - SII services (auth, document, form, sync)
- [backend/app/services/notifications/](backend/app/services/notifications/) - Notification service

### Database Session Management

**Critical rules:**
- Always use `async with` for database sessions in standalone scripts/tasks
- Routers get sessions via `Depends(get_db)` - FastAPI manages lifecycle
- Services receive `db: AsyncSession` as parameter - don't create sessions in services
- Celery tasks must create their own sessions:
  ```python
  from app.config.database import get_db

  async with get_db() as db:
      # Use db here
  ```

See [backend/docs/DATABASE_SESSION_MANAGEMENT.md](backend/docs/DATABASE_SESSION_MANAGEMENT.md) for details.

## Important Implementation Notes

### Production Parity for Development

**Always use `./dev.sh` for backend development** to match production:
- Gunicorn + 2 Uvicorn workers (same as Railway)
- pgbouncer pooler (port 6543) for database connection
- Auto-reload enabled for development
- Same timeout/graceful shutdown settings

This prevents "works on my machine" issues. Direct `uvicorn` usage is not production-like.

### Authentication

- JWT tokens from Supabase
- `get_current_user()` for protected endpoints (returns user_id)
- `get_optional_user()` for ChatKit (allows anonymous)
- WhatsApp webhooks use HMAC validation (no JWT)

### Multi-tenancy

- Most models include `company_id` for tenant isolation
- Row Level Security (RLS) enabled in Supabase
- Some system-level tasks use `company_id=None` (global)

### Testing Conventions

- Backend: pytest in `backend/tests/` (currently minimal)
- Frontend: vitest configured but not heavily used
- SII integration: Real extraction tests require credentials
- Always test with production-parity setup (`./dev.sh`)

### Agent Tool Development

When creating new agent tools:

1. Define tools in `backend/app/agents/tools/{domain}/`
2. Use `@function_tool` decorator
3. Accept `FizkoContext` as first parameter for context access
4. Return structured data (dicts/lists)
5. Handle errors gracefully with try/except
6. Add type hints throughout
7. Register tools with agent in specialized agent file

**Example:**
```python
from chatkit import function_tool
from app.agents.core.context import FizkoContext

@function_tool
async def calculate_iva(
    context: FizkoContext,
    net_amount: float,
    include_iva: bool = True
) -> dict:
    """Calculate IVA (19%) for a given amount."""
    # Implementation
```

### UI Tools (ChatKit Widgets)

For interactive UI components in ChatKit:

1. Define UI tool in `backend/app/agents/ui_tools/tools/`
2. Inherit from `UITool` base class
3. Implement `execute()` method
4. Return `UIToolResult` with `component` and `data`
5. Register in `UIToolDispatcher`

See [backend/app/agents/ui_tools/README.md](backend/app/agents/ui_tools/README.md)

### Common Pitfalls

1. **Database pooling**: Use port 6543 (pgbouncer) in production, NOT 5432
2. **Redis URL format**: Include authentication if needed: `redis://:password@host:port/db`
3. **Async/await**: All DB operations must be async with SQLAlchemy 2.0
4. **Session management**: Never create sessions in services - receive as parameter
5. **CORS**: Allowed origins include localhost, Vercel domains, and fizko.ai domains
6. **File paths**: Always use absolute paths in file references for clickability
7. **WhatsApp formatting**: No markdown in WhatsApp messages - use plain text

## Deployment

### Backend (Railway)

- Uses `backend/Dockerfile` (not in root)
- `backend/railway.json` configures build
- Environment variables set in Railway dashboard
- Automatic deploys on push to `main`
- Database: Use Supabase with pgbouncer pooler (port 6543)

### Frontend (Vercel)

- Uses `vercel.json` in root
- Build command: `cd frontend && npm run build`
- Output directory: `frontend/dist`
- Environment variables set in Vercel dashboard
- Automatic deploys on push to `main`

## Key Files to Reference

- **Backend entry point:** [backend/app/main.py](backend/app/main.py)
- **Agent orchestration:** [backend/app/agents/orchestration/handoffs_manager.py](backend/app/agents/orchestration/handoffs_manager.py)
- **Frontend entry point:** [frontend/src/app/main.tsx](frontend/src/app/main.tsx)
- **Database models:** [backend/app/db/models/](backend/app/db/models/)
- **API routes index:** [backend/app/routers/__init__.py](backend/app/routers/__init__.py)
- **SII client:** [backend/app/integrations/sii/client/](backend/app/integrations/sii/client/)
- **Celery tasks:** [backend/app/infrastructure/celery/tasks/](backend/app/infrastructure/celery/tasks/)

## Getting Help

For deeper context on specific subsystems:
- **Agents:** [backend/app/agents/README.md](backend/app/agents/README.md)
- **SII Integration:** [backend/app/integrations/sii/README.md](backend/app/integrations/sii/README.md)
- **WhatsApp Router:** [backend/app/routers/whatsapp/README.md](backend/app/routers/whatsapp/README.md)
- **Notifications:** [backend/app/services/notifications/README.md](backend/app/services/notifications/README.md)
- **Scheduled Tasks:** [backend/app/services/scheduled_tasks/README.md](backend/app/services/scheduled_tasks/README.md)
- **UI Tools:** [backend/app/agents/ui_tools/README.md](backend/app/agents/ui_tools/README.md)
- **Agent Tools (Widgets):** [backend/app/agents/tools/widgets/README.md](backend/app/agents/tools/widgets/README.md)
