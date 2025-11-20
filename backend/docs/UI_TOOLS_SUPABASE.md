# UI Tools System - Supabase Repository Pattern

This document describes the UI Tools system for backend-v2, which uses the **repository pattern** for modular database access via Supabase.

## Overview

The UI Tools system pre-loads relevant context when users interact with specific UI components, enriching the agent's knowledge before processing requests.

**Key improvements over the original backend:**
- ✅ **Repository pattern** - Modular, domain-specific data access
- ✅ **No SQLAlchemy** - Direct Supabase client with Postgres
- ✅ **Lazy-loaded repositories** - Only instantiated when needed
- ✅ **Type-safe** - Full typing with TYPE_CHECKING guards
- ✅ **Error handling** - Centralized logging and error recovery

## Architecture

```
User clicks UI component
        ↓
Frontend sends: ui_component="contact_card" + entity_id="12-3"
        ↓
Backend: UIToolDispatcher.dispatch()
        ↓
ContactCardTool.process()
        ↓
Uses: supabase.contacts.get_by_rut()  ← Repository pattern!
      supabase.contacts.get_sales_summary()
        ↓
Returns enriched context to agent
        ↓
Agent receives: "## 📇 CONTEXTO: [contact data]"
```

## Repository Pattern

### Structure

```
app/
├── config/
│   └── supabase.py                 # SupabaseClient with repository access
├── repositories/
│   ├── __init__.py                 # Exports all repositories
│   ├── base.py                     # BaseRepository (error handling)
│   ├── calendar.py                 # CalendarRepository
│   ├── companies.py                # CompaniesRepository
│   ├── contacts.py                 # ContactsRepository
│   ├── documents.py                # DocumentsRepository
│   ├── f29.py                      # F29Repository
│   ├── notifications.py            # NotificationsRepository
│   ├── people.py                   # PeopleRepository
│   └── tax_summaries.py            # TaxSummariesRepository
└── agents/
    └── ui_tools/
        ├── core/
        │   ├── base.py             # BaseUITool, UIToolContext
        │   ├── dispatcher.py       # UIToolDispatcher
        │   └── registry.py         # ui_tool_registry
        └── tools/
            ├── contact_card.py     # ContactCardTool (migrated)
            └── ...                 # (other tools to migrate)
```

### SupabaseClient

The `SupabaseClient` provides property-based access to repositories:

```python
from app.config.supabase import get_supabase_client

supabase = get_supabase_client()

# Access repositories via properties
contact = await supabase.contacts.get_by_rut(company_id, rut)
sales = await supabase.documents.get_recent_sales(company_id)
summary = await supabase.tax_summaries.get_iva_summary(company_id)
```

**Available repositories:**
- `supabase.calendar` - Calendar events, templates, tasks, history
- `supabase.companies` - Company data
- `supabase.contacts` - Contacts, sales/purchase summaries, top clients/providers
- `supabase.documents` - Sales and purchase documents
- `supabase.f29` - F29 forms, pending/overdue forms
- `supabase.notifications` - Notifications, templates
- `supabase.people` - People/payroll, employees
- `supabase.tax_summaries` - IVA, revenue, expense summaries

### BaseRepository

All repositories inherit from `BaseRepository`:

```python
class BaseRepository:
    def __init__(self, client: Client):
        self._client = client

    def _log_error(self, operation: str, error: Exception, **context) -> None:
        """Centralized error logging"""

    def _extract_data(self, response, operation: str) -> dict | None:
        """Extract data with error handling"""

    def _extract_data_list(self, response, operation: str) -> list[dict]:
        """Extract list data with error handling"""
```

## Usage in UI Tools

### Example: ContactCardTool

```python
from app.agents.ui_tools.core.base import BaseUITool, UIToolContext, UIToolResult
from app.agents.ui_tools.core.registry import ui_tool_registry

@ui_tool_registry.register
class ContactCardTool(BaseUITool):
    @property
    def component_name(self) -> str:
        return "contact_card"

    async def process(self, context: UIToolContext) -> UIToolResult:
        # Access Supabase via context
        supabase = context.supabase

        # Use repositories for data access
        contact = await supabase.contacts.get_by_rut(
            context.company_id,
            contact_rut
        )

        sales_summary = await supabase.contacts.get_sales_summary(contact["id"])
        purchase_summary = await supabase.contacts.get_purchase_summary(contact["id"])

        # Format and return context
        return UIToolResult(
            success=True,
            context_text=self._format_context(contact, sales_summary, purchase_summary),
            structured_data={...}
        )
```

## API Integration

### FastAPI Router

In [app/routers/chat/agent.py](app/routers/chat/agent.py):

```python
from app.config.supabase import get_supabase_client
from app.agents.ui_tools.core.dispatcher import UIToolDispatcher

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    ui_component: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
) -> ChatResponse:
    # Get Supabase client
    supabase = get_supabase_client()

    # Dispatch to UI tool if component specified
    ui_context_text = ""
    if ui_component and ui_component != "null":
        additional_data = {}
        if entity_id:
            additional_data["entity_id"] = entity_id
        if entity_type:
            additional_data["entity_type"] = entity_type

        ui_tool_result = await UIToolDispatcher.dispatch(
            ui_component=ui_component,
            user_message=request.message,
            company_id=request.company_id,
            user_id=request.user_id,
            supabase=supabase,
            additional_data=additional_data
        )

        if ui_tool_result and ui_tool_result.success:
            ui_context_text = ui_tool_result.context_text

    # Agent receives enriched context
    ...
```

### Frontend Integration

Frontend sends query parameters:

```typescript
// User clicks contact card
const response = await fetch(
  `/api/chat?ui_component=contact_card&entity_id=${contact.rut}`,
  {
    method: "POST",
    body: JSON.stringify({
      message: "Cuéntame sobre este contacto",
      company_id: currentCompany.id,
      user_id: currentUser.id
    })
  }
);
```

## Creating New UI Tools

### 1. Choose the Right Repositories

Determine which repositories your tool needs:

```python
# For contact data
supabase.contacts.get_by_rut()
supabase.contacts.get_sales_summary()

# For documents
supabase.documents.get_sales_document()
supabase.documents.get_recent_sales()

# For tax summaries
supabase.tax_summaries.get_iva_summary()
supabase.tax_summaries.get_revenue_summary()
```

### 2. Create the Tool

```python
# app/agents/ui_tools/tools/my_new_tool.py

from app.agents.ui_tools.core.base import BaseUITool, UIToolContext, UIToolResult
from app.agents.ui_tools.core.registry import ui_tool_registry

@ui_tool_registry.register
class MyNewTool(BaseUITool):
    @property
    def component_name(self) -> str:
        return "my_component"

    @property
    def description(self) -> str:
        return "Describe what this tool does"

    @property
    def agent_instructions(self) -> str:
        return """
        ## 💡 INSTRUCCIONES: My Component

        Explain to the agent what context they have and how to use it.
        """.strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        if not context.supabase or not context.company_id:
            return UIToolResult(success=False, error="Missing context")

        # Use repositories
        data = await context.supabase.my_repo.get_data(context.company_id)

        return UIToolResult(
            success=True,
            context_text=self._format_context(data),
            structured_data=data
        )

    def _format_context(self, data: dict) -> str:
        return f"## Context for agent\n\n{data}"
```

### 3. Register the Tool

Import in [app/agents/ui_tools/tools/__init__.py](app/agents/ui_tools/tools/__init__.py):

```python
from .my_new_tool import MyNewTool

__all__ = [
    "ContactCardTool",
    "MyNewTool",  # Add here
]
```

Import in [app/agents/ui_tools/__init__.py](app/agents/ui_tools/__init__.py):

```python
from .tools import (
    ContactCardTool,
    MyNewTool,  # Add here
)

__all__ = [
    # ...
    "MyNewTool",  # Add here
]
```

## Repository Methods Reference

### ContactsRepository

```python
# Get contact
contact = await supabase.contacts.get_by_rut(company_id, rut)
contact = await supabase.contacts.get_by_id(contact_id)

# Summaries
sales_summary = await supabase.contacts.get_sales_summary(contact_id)
# Returns: {"total_amount": float, "document_count": int}

purchase_summary = await supabase.contacts.get_purchase_summary(contact_id)
# Returns: {"total_amount": float, "document_count": int}

# Top contacts
top_clients = await supabase.contacts.get_top_clients(company_id, limit=5)
top_providers = await supabase.contacts.get_top_providers(company_id, limit=5)
```

### DocumentsRepository

```python
# Get documents
doc = await supabase.documents.get_sales_document(doc_id, include_contact=True)
doc = await supabase.documents.get_purchase_document(doc_id, include_contact=True)

# Lists
sales = await supabase.documents.get_recent_sales(company_id, limit=10)
purchases = await supabase.documents.get_recent_purchases(company_id, limit=10)

# By contact
sales = await supabase.documents.get_sales_by_contact(contact_id, limit=50)
purchases = await supabase.documents.get_purchases_by_contact(contact_id, limit=50)

# By type
docs = await supabase.documents.get_documents_by_type(
    company_id,
    document_type="sales",  # or "purchase"
    tipo_dte="33",  # Optional: filter by DTE type
    limit=100
)
```

### TaxSummariesRepository

```python
# Comprehensive summary
summary = await supabase.tax_summaries.get_tax_summary(company_id, period="202501")
# Returns: {"iva": {...}, "revenue": {...}, "expenses": {...}, "period": "202501"}

# Individual summaries
iva = await supabase.tax_summaries.get_iva_summary(company_id, period="202501")
# Returns: {"debito_fiscal": float, "credito_fiscal": float, "balance": float, ...}

revenue = await supabase.tax_summaries.get_revenue_summary(company_id, period="202501")
# Returns: {"total_revenue": float, "net_revenue": float, "document_count": int}

expenses = await supabase.tax_summaries.get_expense_summary(company_id, period="202501")
# Returns: {"total_expenses": float, "net_expenses": float, "document_count": int}

# Trends
trend = await supabase.tax_summaries.get_monthly_revenue_trend(company_id, months=6)
# Returns: [{"month": "202501", "revenue": float}, ...]
```

### NotificationsRepository

```python
# Get notification
notif = await supabase.notifications.get_by_id(notif_id, include_template=True)

# By company
notifs = await supabase.notifications.get_by_company(
    company_id,
    limit=50,
    status="pending"  # or "sent", "failed"
)

# Pending
pending = await supabase.notifications.get_pending(company_id, limit=100)

# Templates
template = await supabase.notifications.get_template_by_code("f29_reminder")
templates = await supabase.notifications.get_all_templates()

# By template
recent = await supabase.notifications.get_recent_by_template(
    company_id,
    template_code="f29_reminder",
    limit=10
)
```

### CalendarRepository

```python
# Get event
event = await supabase.calendar.get_event_by_id(
    event_id,
    include_template=True,
    include_tasks=True,
    include_history=False
)

# By company
events = await supabase.calendar.get_events_by_company(
    company_id,
    limit=50,
    status="pending",  # or "completed", "cancelled"
    include_template=True
)

# Upcoming
upcoming = await supabase.calendar.get_upcoming_events(
    company_id,
    days_ahead=30,
    limit=20
)

# Templates
template = await supabase.calendar.get_event_template_by_code("f29_payment")
templates = await supabase.calendar.get_all_event_templates()

# Tasks and history
tasks = await supabase.calendar.get_event_tasks(event_id)
history = await supabase.calendar.get_event_history(event_id, limit=20)
```

### F29Repository

```python
# Get form
form = await supabase.f29.get_form_by_id(form_id)
form = await supabase.f29.get_form_by_period(company_id, period="202501")
latest = await supabase.f29.get_latest_form(company_id)

# Lists
forms = await supabase.f29.get_forms_by_company(
    company_id,
    limit=12,
    status="pending"  # or "paid", "overdue"
)

pending = await supabase.f29.get_pending_forms(company_id, limit=50)
overdue = await supabase.f29.get_overdue_forms(company_id, limit=50)

# Payment history
history = await supabase.f29.get_payment_history(company_id, limit=12)
```

### PeopleRepository

```python
# Get person
person = await supabase.people.get_person_by_id(person_id)
person = await supabase.people.get_person_by_rut(company_id, rut)

# Lists
people = await supabase.people.get_people_by_company(
    company_id,
    status="active",  # or "inactive"
    limit=100
)

employees = await supabase.people.get_active_employees(company_id, limit=100)

# Count
count = await supabase.people.get_employee_count(company_id)

# Summary
summary = await supabase.people.get_payroll_summary(company_id, period="202501")

# Search
results = await supabase.people.search_people(company_id, query="juan", limit=20)
```

### CompaniesRepository

```python
# Get company
company = await supabase.companies.get_by_id(company_id)
company = await supabase.companies.get_by_rut(rut)

# Lists
companies = await supabase.companies.get_all(limit=100)

# Search
results = await supabase.companies.search_by_name(query="acme", limit=20)
```

## Environment Variables

Required in [backend-v2/.env](backend-v2/.env):

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...  # For backend operations (bypasses RLS)
SUPABASE_ANON_KEY=eyJhbGc...     # Fallback (respects RLS)

# OpenAI (for agents)
OPENAI_API_KEY=sk-proj-...

# SII credentials (for Selenium integration)
STC_TEST_RUT=12345678
STC_TEST_DV=9
STC_TEST_PASSWORD=...
SII_HEADLESS=true
```

## Migration Status

### ✅ Migrated to Repository Pattern
- [x] **ContactCardTool** - Uses `supabase.contacts` repository

### 🔄 To Be Migrated
These tools exist in the original backend but need migration to Supabase + repositories:

- [ ] **TaxSummaryIVATool** - Use `supabase.tax_summaries.get_iva_summary()`
- [ ] **TaxSummaryRevenueTool** - Use `supabase.tax_summaries.get_revenue_summary()`
- [ ] **TaxSummaryExpensesTool** - Use `supabase.tax_summaries.get_expense_summary()`
- [ ] **DocumentDetailTool** - Use `supabase.documents.get_sales_document()` / `get_purchase_document()`
- [ ] **PersonDetailTool** - Use `supabase.people.get_person_by_rut()`
- [ ] **NotificationCalendarEventTool** - Use `supabase.calendar.get_event_by_id()`
- [ ] **NotificationGenericTool** - Use `supabase.notifications.get_by_id()`
- [ ] **TaxCalendarEventTool** - Use `supabase.calendar.get_event_by_id()`
- [ ] **F29FormCardTool** - Use `supabase.f29.get_form_by_period()`
- [ ] **PayLatestF29Tool** - Use `supabase.f29.get_latest_form()`
- [ ] **AddEmployeeButtonTool** - Use `supabase.people.get_active_employees()`

### Migration Steps for Each Tool

1. Read original tool from [backend/app/agents/ui_tools/tools/](../backend/app/agents/ui_tools/tools/)
2. Identify SQLAlchemy queries (e.g., `db.execute(select(...))`)
3. Replace with repository methods (e.g., `supabase.documents.get_sales_document()`)
4. Update data structure mapping (repository returns dicts, not ORM objects)
5. Add error handling for `None` responses
6. Test with mock data or real Supabase instance
7. Enable in [app/agents/ui_tools/tools/__init__.py](app/agents/ui_tools/tools/__init__.py)

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'sqlalchemy'`

**Solution**: Check that tool is not importing SQLAlchemy:
```python
# ❌ Bad
from sqlalchemy import select

# ✅ Good
# No SQLAlchemy imports needed with repository pattern
```

### Type Errors with SupabaseClient

**Problem**: Type checker complains about repository attributes

**Solution**: Use `TYPE_CHECKING` guard:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config.supabase import SupabaseClient

class UIToolContext(BaseModel):
    supabase: "SupabaseClient | None" = None  # String annotation
```

### Repository Returns None

**Problem**: Repository method returns `None` instead of expected data

**Solution**: Add defensive checks:
```python
summary = await supabase.contacts.get_sales_summary(contact_id)
if summary is None:
    summary = {"total_amount": 0, "document_count": 0}
```

### Lazy Loading Errors

**Problem**: Repository not initialized when accessed

**Solution**: Repositories are lazy-loaded via properties - they initialize on first access. No manual initialization needed:
```python
# This works - repository is created on first access
contact = await supabase.contacts.get_by_rut(company_id, rut)
```

## Best Practices

### 1. Use Repositories, Not Raw Client

```python
# ❌ Bad - direct client access
response = supabase.client.table("contacts").select("*").eq("rut", rut).execute()

# ✅ Good - use repository
contact = await supabase.contacts.get_by_rut(company_id, rut)
```

### 2. Handle None Responses

```python
# ❌ Bad - assumes data exists
total = summary["total_amount"]

# ✅ Good - defensive
summary = await supabase.contacts.get_sales_summary(contact_id)
if summary is None:
    summary = {"total_amount": 0, "document_count": 0}
total = summary.get("total_amount", 0)
```

### 3. Use Type Hints

```python
# ✅ Good - fully typed
async def get_contact_data(
    supabase: SupabaseClient,
    company_id: str,
    rut: str
) -> dict[str, Any] | None:
    contact = await supabase.contacts.get_by_rut(company_id, rut)
    return contact
```

### 4. Log Errors in Tools

```python
try:
    contact = await supabase.contacts.get_by_rut(company_id, rut)
except Exception as e:
    self.logger.error(f"Failed to fetch contact: {e}", exc_info=True)
    return UIToolResult(success=False, error=str(e))
```

### 5. Format Context Clearly

```python
def _format_context(self, data: dict) -> str:
    return f"""
## 📇 CONTEXTO: {data["name"]}

**Key Info:**
- Field 1: {data["field1"]}
- Field 2: {data["field2"]}

Use this info to answer user questions.
    """.strip()
```

## Next Steps

1. **Migrate remaining UI Tools** - Follow migration steps above for each tool
2. **Add new repositories** - If new data domains are needed, create new repository classes
3. **Optimize queries** - Add database indexes, use Supabase RPC functions for complex aggregations
4. **Add caching** - Consider caching frequently accessed data (company info, templates)
5. **Write tests** - Add unit tests for repositories and integration tests for UI tools

## References

- [Original UI Tools](../backend/app/agents/ui_tools/README.md) - Original SQLAlchemy-based implementation
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html) - Martin Fowler's pattern description
- [Supabase Python Docs](https://supabase.com/docs/reference/python/introduction) - Official Supabase Python client
