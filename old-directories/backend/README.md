# Fizko Backend

Fizko is a tax/accounting platform for small businesses in Chile, built with FastAPI, OpenAI ChatKit, and a multi-agent AI system.

## Architecture Overview

The Fizko backend is based on the **impor-ai** multi-agent architecture but adapted for tax and accounting use cases:

- **Multi-agent system**: Triage agent routes to 2 specialized agents
- **ChatKit integration**: Conversational AI interface
- **PostgreSQL/Supabase**: Database and authentication
- **Async patterns**: SQLAlchemy 2.0 with asyncpg

## Project Structure

```
backend/
├── app/
│   ├── agents/                  # Multi-agent system
│   │   ├── specialized/         # Specialized agents (2 agents)
│   │   │   ├── sii_general_agent.py      # SII tax authority expert
│   │   │   └── remuneraciones_agent.py   # Payroll calculations expert
│   │   ├── chat.py              # FizkoServer (ChatKit integration)
│   │   ├── context.py           # FizkoContext for agents
│   │   ├── triage_agent.py      # Router agent
│   │   ├── lazy_handoffs.py     # Request-scoped agent manager
│   │   ├── multi_agent_system.py # Orchestrator
│   │   └── tools/               # Agent tools (empty for now)
│   ├── config/                  # Configuration & constants
│   │   ├── constants.py         # MODEL, agent instructions
│   │   └── database.py          # SQLAlchemy async engine
│   ├── core/                    # Auth utilities
│   │   └── auth.py              # JWT authentication
│   ├── db/                      # Database models
│   │   ├── models.py            # Fizko-specific models
│   │   └── supabase.py          # Supabase client
│   ├── routers/                 # FastAPI route handlers
│   │   ├── companies.py         # Company management
│   │   ├── tax_documents.py     # Tax documents
│   │   ├── payroll.py           # Payroll records
│   │   └── conversations.py     # Chat conversations
│   ├── stores/                  # Conversation persistence
│   │   ├── memory_store.py      # In-memory store
│   │   └── supabase_store.py    # Supabase persistence
│   ├── services/                # Business logic services
│   ├── dependencies.py          # Shared dependencies
│   └── main.py                  # FastAPI application
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore file
├── pyproject.toml               # Python dependencies (uv)
└── README.md                    # This file
```

## Database Models

### Core Models (from impor-ai)
- **Profile**: User accounts (extends Supabase auth.users)
- **Conversation**: Chat threads with ChatKit session IDs
- **Message**: Individual messages in conversations
- **ChatKitAttachment**: File upload metadata

### Fizko-Specific Models (NEW)
- **Company**: Company information (RUT, business name, tax regime)
- **TaxDocument**: Tax documents (invoices, receipts, etc.)
- **PayrollRecord**: Salary records with deductions
- **TaxSummary**: Financial summaries (monthly/quarterly/annual)

## Multi-Agent System

### Agents

1. **Triage Agent** (`triage_agent.py`)
   - Routes user queries to specialized agents
   - Keywords: "IVA", "impuestos" → SII General
   - Keywords: "sueldo", "nómina", "AFP" → Remuneraciones

2. **SII General Agent** (`sii_general_agent.py`)
   - General tax questions about Chilean SII
   - Tax filing deadlines
   - Tax regime explanations (14 A, 14 B, ProPyme, 14 ter)
   - IVA calculations

3. **Remuneraciones Agent** (`remuneraciones_agent.py`)
   - Salary calculations (net salary from gross)
   - Employer contributions
   - Payroll record management
   - Chilean labor law compliance

### Request Flow

```
User Query
    ↓
POST /chatkit
    ↓
FizkoServer.respond()
    ↓
LazyHandoffsManager.get_triage_agent()
    ↓
Triage Agent analyzes intent
    ↓
Handoff to specialized agent
    ↓
Agent uses tools (DB queries, calculations)
    ↓
Stream response back to user
```

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# OR using pip
pip install -e .
```

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Required variables:
- `OPENAI_API_KEY`: OpenAI API key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anon key
- `SUPABASE_JWT_SECRET`: Supabase JWT secret
- `DATABASE_URL`: PostgreSQL connection string

### 3. Database Setup

Create tables in Supabase using the SQL schema:

```sql
-- See migrations/ folder for SQL scripts
-- Or use SQLAlchemy to create tables:
-- await init_db()  # From config/database.py
```

### 4. Run the Server

**IMPORTANT:** Local development now uses **production-parity configuration** to avoid "works on my machine" issues.

#### Recommended: Use the dev.sh script (Production Parity ✅)

```bash
# This runs with the SAME configuration as production:
# - Gunicorn + 2 Uvicorn workers
# - pgbouncer pooler (port 6543)
# - Auto-reload enabled
./dev.sh
```

#### Alternative: Manual commands

```bash
# Option A: Production parity (Gunicorn)
uv run gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8089 \
  --reload

# Option B: Quick development (Uvicorn only - NOT production-like)
uv run uvicorn app.main:app --reload --port 8089
```

The API will be available at:
- API: `http://localhost:8089`
- Docs: `http://localhost:8089/docs`
- Health: `http://localhost:8089/health`

### 5. Production Parity Checklist

To ensure your local environment matches production:

- ✅ **Database:** Use port **6543** (pgbouncer pooler), NOT 5432
  ```
  DATABASE_URL=postgresql+asyncpg://user:pass@db.project.supabase.co:6543/postgres?sslmode=require
  ```

- ✅ **Server:** Use **Gunicorn + Uvicorn workers** (via `./dev.sh`)
  - 2 workers (same as Railway Starter)
  - Auto-reload enabled for development
  - Same timeout/graceful shutdown settings

- ✅ **Environment:** Same `.env` variables as Railway
  - All SUPABASE_* variables
  - OPENAI_API_KEY
  - ENCRYPTION_KEY
  - ALLOWED_ORIGINS

**Why production parity matters:**
- pgbouncer (6543) disables prepared statements → local tests this behavior
- Gunicorn manages workers → local tests process crashes/restarts
- Same SSL/pooling settings → no DB connection surprises in production

## API Endpoints

### ChatKit
- `POST /chatkit` - Conversational AI endpoint

### Companies
- `GET /companies` - List user's companies
- `GET /companies/{id}` - Get company details
- `POST /companies` - Create new company

### Tax Documents
- `GET /tax-documents` - List tax documents
- `GET /tax-documents/{id}` - Get document details

### Payroll
- `GET /payroll` - List payroll records
- `GET /payroll/{id}` - Get payroll details

### Conversations
- `GET /conversations` - List conversations
- `GET /conversations/{id}` - Get conversation details

## Agent Tools

### Company Information
**Note:** Company information (RUT, business name, tax regime, etc.) is automatically loaded at the start of each conversation and available in the agent context. No tool call is needed.

### SII General Agent Tools
- `get_tax_regime_info(regime)` - Get tax regime information
- `get_tax_deadlines(month)` - Get filing deadlines
- `calculate_iva(net_amount, include_iva)` - Calculate IVA (19%)

### Remuneraciones Agent Tools
- `calculate_salary(base_salary, bonuses, overtime)` - Calculate net salary
- `calculate_employer_contributions(base_salary)` - Calculate employer costs
- `save_payroll_record(...)` - Save payroll to database
- `get_payroll_records(company_id, period_year, period_month)` - Get payroll records

## Key Differences from impor-ai

### Removed
- Alibaba integration
- Quotation sourcing tools
- Logistics/customs agents
- HS code references
- Exchange rates
- Product collection
- Step management system
- Knowledge base extraction

### Added
- Company management
- Tax document tracking
- Payroll calculations
- SII-specific tax tools
- Chilean tax regime support
- IVA calculation utilities

### Adapted
- Database models (Company, TaxDocument, PayrollRecord instead of Quotation, QuotationProduct)
- Agent instructions (tax/accounting focus instead of import/logistics)
- Tools (tax calculations instead of import costs)

## Development Notes

### Code Style
- Follows impor-ai patterns (async/await, lazy handoffs, request-scoped DB sessions)
- Uses `@function_tool` decorators for agent tools
- SQLAlchemy 2.0 async patterns
- Type hints throughout

### Authentication
- JWT tokens from Supabase
- `get_current_user()` for protected endpoints
- `get_optional_user()` for ChatKit (allows anonymous)

### Session Management
- ChatKit conversations persisted to PostgreSQL
- SQLiteSession for agent conversation history
- Lazy agent initialization per thread

## Testing

```bash
# Test the health endpoint
curl http://localhost:8089/health

# Test ChatKit endpoint (requires auth token)
curl -X POST http://localhost:8089/chatkit \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"op": "create_thread"}'
```

## Production Deployment

1. Set environment variables in your hosting platform
2. Use PostgreSQL (not SQLite)
3. Enable HTTPS
4. Set proper CORS origins in `main.py`
5. Use production-grade ASGI server (uvicorn with workers)

## License

[Your License]

## Support

For issues or questions, contact [Your Contact Info]
