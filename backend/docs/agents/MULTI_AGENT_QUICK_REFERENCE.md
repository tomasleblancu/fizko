# FIZKO MULTI-AGENT SYSTEM - QUICK REFERENCE

## System Overview

**Type:** Supervisor + 7 Specialized Agents using OpenAI Agents SDK
**Entry Point:** Supervisor Agent (gpt-4o-mini)
**Architecture:** Thread-scoped, request-cached, subscription-aware

```
User Message
  ↓
[UI Tool Context Injection]
  ↓
[Guardrail Validation]
  ↓
Supervisor Agent (routes intent)
  ↓
Specialized Agent (executes domain logic)
  ↓
Response with widgets/data
```

## Core Components

### 1. Orchestration Layer
- **HandoffsManager** (`orchestration/handoffs_manager.py`)
  - Global singleton, caches orchestrators per thread_id
  - Entry point: `get_supervisor_agent(thread_id, db, company_id, ...)`
  - Cache prevents agent state loss across requests

- **MultiAgentOrchestrator** (`orchestration/multi_agent_orchestrator.py`)
  - Creates all agents (supervisor + available specialists)
  - Configures handoffs between agents
  - Integrates subscription validation and session management

- **AgentFactory** (`orchestration/agent_factory.py`)
  - Conditional agent creation based on subscription
  - Only creates supervisor + agents in availability list

- **HandoffFactory** (`orchestration/handoff_factory.py`)
  - Creates validated handoffs with subscription checking
  - Returns block response if agent unavailable
  - Tracks active agent via SessionManager

- **SubscriptionValidator** (`orchestration/subscription_validator.py`)
  - Maps company subscription to available agents
  - Queries SubscriptionGuard for access control

- **SessionManager** (`orchestration/session_manager.py`)
  - In-memory tracking of active agent per thread
  - Enables agent persistence across messages

### 2. Agent Definitions

**Supervisor Agent (gpt-4o-mini)**
- Pure router, no database access
- Tools: show_subscription_upgrade()
- Guardrails: abuse_detection

**7 Specialized Agents (gpt-4.1-mini or gpt-5-nano)**
| Agent | Purpose |
|-------|---------|
| general_knowledge | Tax concepts, theory |
| tax_documents | Real document data |
| monthly_taxes | F29 form expertise |
| payroll | Labor law, employees |
| settings | User preferences |
| expense | Manual expense entry |
| feedback | Bug reports, feature requests |

### 3. Tools System

**Location:** `backend/app/agents/tools/`

**Categories:**
- `tax/` - Tax document queries, F29, expenses
- `payroll/` - Employee management
- `settings/` - Notifications, preferences
- `widgets/` - F29 display, payroll views
- `memory/` - User and company memory
- `feedback/` - Feedback collection

**Pattern:** `@function_tool` decorator on async functions
- First param always `FizkoContext`
- Type hints required
- Returns structured data

### 4. UI Tools System

**Purpose:** Pre-fetch component-specific context before agent execution

**Architecture:**
```
Frontend: ui_component="contact_card"
  ↓
UIToolDispatcher.dispatch()
  ↓
ContactCardTool.process(UIToolContext)
  ↓
Returns UIToolResult with:
  - context_text (prepended to agent instructions)
  - structured_data (available to agent)
  - widget (optional immediate render)
```

**Key Classes:**
- `BaseUITool` - Abstract base with @property methods
- `UIToolContext` - Input data
- `UIToolResult` - Output with context + data
- `UIToolRegistry` - Auto-discovery via @register decorator
- `UIToolDispatcher` - Routes by component_name

**Current Tools:** contact_card, tax_summary_*, document_detail, person_detail, f29_form_card, notifications, etc.

### 5. Context & State

**FizkoContext** (`core/context.py`)
- Extends ChatKit's AgentContext
- Carries: current_agent_type, thread_item_converter, company_info
- Auto-populated with company data

**Company Info Loading** (`core/context_loader.py`)
- `load_company_info()` - Fetches company + tax info
- 30-minute TTL in-memory cache
- Automatically formatted as XML context

**Attachment Stores:**
- `MemoryAttachmentStore` - Dev/single instance
- `SupabaseAttachmentStore` - Production/multi-instance
- Tracks metadata, content, OpenAI vector_store_id

### 6. Security

**Multi-Layer Subscription Control:**
1. Orchestration level: Only create allowed agents
2. Handoff level: Validate agent exists
3. Agent level: show_subscription_upgrade() tool

**Guardrails:**
- Input: abuse_detection, PII detection, subscription check
- Output: (not heavily implemented)
- Execution: Parallel asyncio execution

**Row-Level Security (RLS):**
- Implemented at Supabase level
- Each table filtered by company_id

## Key Data Flows

### Request → Response
1. Authenticate + load company_id
2. Optional: UIToolDispatcher enriches context
3. Optional: Input guardrails validate
4. Get supervisor via HandoffsManager
5. Build FizkoContext with company_info
6. Runner executes: supervisor → handoff → specialist
7. Specialist uses tools, returns response
8. Format for channel (ChatKit vs WhatsApp)

### Company Data Loading
- Context creation → load_company_info()
- Cache check (30-min TTL)
- Query Company + CompanyTaxInfo if miss
- Format as XML, inject into instructions

### Agent Handoff
1. Supervisor calls handoff tool
2. HandoffFactory.create_validated_handoff() triggered
3. Check agent in agents dict
4. If missing: return block_response (show upgrade)
5. If present: Update SessionManager, execute agent

## Configuration

**Models:** (`config/constants.py`)
- SUPERVISOR_MODEL = "gpt-4o-mini"
- SPECIALIZED_MODEL = "gpt-4.1-mini"
- REASONING_EFFORT = "low"

**Subscription Scopes:** (`config/scopes.py`)
- free: [] (limited)
- basic: [tax_documents, payroll, settings]
- pro: [all agents]

**Instructions:** `instructions/{agent_name}/`
- Modular structure: `0_core.md`, `1_context.md`, etc.
- Loaded by glob in `instructions/__init__.py`

## Common Patterns

| Pattern | Use |
|---------|-----|
| Singleton | HandoffsManager, UIToolRegistry |
| Factory | AgentFactory, HandoffFactory |
| Observer | SessionManager, GuardrailRunner |
| Strategy | UI Tools, Attachment stores |
| Decorator | @function_tool, @ui_tool_registry.register |
| Lazy Init | HandoffsManager cache |
| Template Method | BaseUITool |
| DI | Agent creation, context |

## Extension Points

**Add New Specialized Agent:**
1. Create `specialized/new_agent.py`
2. Add to `specialized/__init__.py`
3. Update `AgentFactory.create_available_agents()`
4. Add to `HandoffFactory.get_standard_configs()`

**Add New Tool:**
1. Create in `tools/{domain}/new_tool.py`
2. Decorate with `@function_tool`
3. Import in agent definition

**Add New UI Tool:**
1. Create in `ui_tools/tools/new_component.py`
2. Subclass `BaseUITool`, implement `component_name` and `process()`
3. Decorate with `@ui_tool_registry.register`
4. Import in `ui_tools/__init__.py`

## Critical Issues

1. **Unbounded Cache Growth**
   - HandoffsManager._orchestrator_cache has no size limit
   - Solution: Use TTLCache with maxsize=1000

2. **Non-Persistent Session State**
   - SessionManager in-memory only
   - Lost if orchestrator cache cleared
   - Solution: Persist to Redis for multi-instance

3. **Orchestrator Creation Overhead**
   - ~0.5s per new thread
   - Solution: Cache agent factory, pre-create supervisor

## Performance Notes

- Company info load (cache hit): ~3ms
- Company info load (miss): ~50ms
- Orchestrator creation: ~500ms
- Agent execution: Depends on tools (no hard limit)

---

**Full Documentation:** See `MULTI_AGENT_ARCHITECTURE.md` in repo root
