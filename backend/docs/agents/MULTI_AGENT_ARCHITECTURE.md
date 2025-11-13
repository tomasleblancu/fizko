# FIZKO MULTI-AGENT SYSTEM ARCHITECTURE ANALYSIS

## Executive Summary

Fizko implements a **supervisor + specialized agents** multi-agent system using OpenAI's Agents SDK. The system routes user queries to domain-specific agents via a smart supervisor, with comprehensive orchestration, subscription-based access control, guardrails for safety, and UI tools for component-driven context enrichment.

**Key Architecture:**
- **Entry Point:** Supervisor Agent (gpt-4o-mini)
- **Specialized Agents:** 7 domain-specific agents (gpt-4.1-mini or gpt-5-nano)
- **Orchestration:** Thread-scoped, cached per request with handoff support
- **Security:** Subscription validation, guardrails, RLS policies
- **Context:** FizkoContext with auto-loaded company info and attachment stores
- **Integration:** Works with ChatKit (web), WhatsApp, and extensible to other channels

---

## 1. CORE ARCHITECTURE

### 1.1 High-Level Flow

```
User Message (ChatKit/WhatsApp)
    ↓
ChatKit Router / WhatsApp Handler
    ↓
[UI Tool Dispatch - enriches context]
    ↓
[Guardrail Check - input validation]
    ↓
HandoffsManager.get_supervisor_agent()
    ↓
MultiAgentOrchestrator.create_multi_agent_orchestrator()
    ├─→ SubscriptionValidator (determines available agents)
    ├─→ AgentFactory (instantiates supervisor + available agents)
    ├─→ HandoffFactory (configures handoffs)
    └─→ SessionManager (tracks active agent per thread)
    ↓
Supervisor Agent evaluates intent → routes to specialist
    ↓
Specialized Agent (payroll, tax_documents, etc.)
    ├─→ Executes tools (database queries, file search, widgets)
    ├─→ Returns response with UI widgets if applicable
    └─→ [Optional handoff back to supervisor]
    ↓
Response → ChatKit/WhatsApp Formatter
    ↓
User Response (text + widgets)
```

### 1.2 Request Lifecycle

1. **Request Enters:** ChatKit router or WhatsApp webhook
2. **Authentication:** User validated via JWT or WhatsApp HMAC
3. **UI Tool Dispatch:** Optional `UIToolDispatcher.dispatch()` for context enrichment
4. **HandoffsManager:** Gets/creates cached orchestrator for thread
5. **Subscription Check:** `SubscriptionValidator` determines which agents to create
6. **Agent Creation:** `AgentFactory` instantiates only allowed agents
7. **Handoff Config:** `HandoffFactory` configures supervisor handoffs
8. **Agent Execution:** Runner handles streaming/non-streaming execution
9. **Output Processing:** Format response for channel

### 1.3 Key Design Patterns

#### Lazy Initialization + Caching
```
HandoffsManager._orchestrator_cache[thread_id] → MultiAgentOrchestrator
```
- Orchestrators created on-demand (need DB + OpenAI client from request)
- Cached per thread_id to maintain agent state across messages
- Cache keys by thread_id ensures isolation

#### Dependency Injection
- All agents receive `db: AsyncSession`, `openai_client: AsyncOpenAI`
- Services receive DB but don't create sessions (stateless)
- Context passed via `FizkoContext` (ChatKit's AgentContext subclass)

#### Factory Pattern
- `AgentFactory`: Creates available agents based on subscription
- `HandoffFactory`: Creates handoff configurations
- Each factory isolates creation logic from orchestration

#### Observer Pattern
- `SessionManager`: Tracks active agent state per thread
- `UIToolRegistry`: Registry pattern for tool discovery
- Guardrails runners execute guardrails in parallel

---

## 2. ORCHESTRATION SYSTEM

### 2.1 HandoffsManager - Request-Scoped Orchestration

**File:** `backend/app/agents/orchestration/handoffs_manager.py`

**Responsibility:** Manage lazy-initialized orchestrators per thread

```python
class HandoffsManager:
    _orchestrator_cache: dict[str, Any]  # thread_id → orchestrator
    
    async def get_orchestrator(thread_id, db, user_id, company_id, ...)
    async def get_supervisor_agent(thread_id, db, ...)
    async def get_all_agents(thread_id, db, ...)
```

**Key Methods:**
- `get_orchestrator()`: Returns cached or creates new orchestrator
- `get_supervisor_agent()`: Entry point for agents system
- `get_all_agents()`: Returns all agents for handoff support
- `clear_cache()`: Invalidates thread cache on session end

**Singleton Instance:** Global `handoffs_manager` available everywhere

**Critical Design Detail:**
The orchestrator is cached per thread_id because:
1. MultiAgentOrchestrator contains Agent instances
2. Agent state (conversation history) must persist across requests
3. Handoffs reference the same agent instances
4. Recreating agents would reset state

### 2.2 MultiAgentOrchestrator - Agent Coordination

**File:** `backend/app/agents/orchestration/multi_agent_orchestrator.py`

**Responsibility:** Create and manage agent network with handoffs

```python
class MultiAgentOrchestrator:
    agents: dict[str, Agent]  # supervisor_agent, tax_documents_agent, etc.
    session_manager: SessionManager  # tracks active agent
    
    def _initialize_agents(self):
        # 1. Create agents via AgentFactory
        # 2. Configure supervisor handoffs
        # 3. Configure bidirectional handoffs (disabled by default)
```

**Architecture:**
```
Supervisor Agent (gpt-4o-mini) ⭐ ENTRY POINT
    ├─→ General Knowledge Agent (gpt-4.1-mini)
    ├─→ Tax Documents Agent (gpt-4.1-mini)
    ├─→ Monthly Taxes Agent (gpt-4.1-mini)
    ├─→ Payroll Agent (gpt-4.1-mini)
    ├─→ Settings Agent (gpt-4.1-mini)
    ├─→ Expense Agent (gpt-4.1-mini)
    └─→ Feedback Agent (gpt-4.1-mini)
```

**Agent Creation:** Only agents in available list are created (subscription-based)

**Handoff Configuration:**
1. Supervisor → Specialized (one-way, always enabled)
2. Specialized → Supervisor (bidirectional, disabled by default)

### 2.3 AgentFactory - Conditional Agent Creation

**File:** `backend/app/agents/orchestration/agent_factory.py`

**Pattern:** Factory method pattern with subscription-aware instantiation

```python
def create_available_agents(available_agent_names: list[str]) -> dict[str, Agent]:
    agents = {}
    agents["supervisor_agent"] = create_supervisor_agent(...)
    
    if "general_knowledge" in available_agent_names:
        agents["general_knowledge_agent"] = create_general_knowledge_agent(...)
    if "tax_documents" in available_agent_names:
        agents["tax_documents_agent"] = create_tax_documents_agent(...)
    # ... etc
    
    return agents
```

**Key Design:**
- Always creates supervisor
- Only creates agents if in allowed list
- Prevents invalid handoffs to unavailable agents

### 2.4 HandoffFactory - Dynamic Handoff Creation

**File:** `backend/app/agents/orchestration/handoff_factory.py`

**Responsibility:** Create validated handoffs with subscription checking

**Handoff Types:**
1. **Supervisor → Specialist:** Routes based on intent
2. **Specialist → Supervisor:** Returns control for topic changes

**Key Features:**
- Validates agent exists before creating handoff
- Subscription check on handoff execution
- Returns blocking response if agent unavailable
- Tracks active agent via SessionManager
- Logs handoff events with icons (🧠 → 📄, etc.)

**Example Configuration:**
```python
HandoffConfig(
    agent_name="payroll",
    agent_key="payroll_agent",
    display_name="Payroll",
    icon="💼",
    description="Transfer to Payroll expert for labor law questions..."
)
```

### 2.5 SubscriptionValidator - Access Control

**File:** `backend/app/agents/orchestration/subscription_validator.py`

**Responsibility:** Determine which agents are available based on subscription

```python
async def get_available_agents(company_id: UUID | None) -> list[str]:
    if not company_id:
        return all_agents  # Anonymous/testing: all access
    
    available = await self.guard.get_available_agents(company_id)
    return available
```

**Integration with SubscriptionGuard:**
- Queries Supabase for company subscription
- Maps subscription tier to available agents
- Handles missing companies gracefully

**Subscription Tiers:** (from `config/scopes.py`)
- **Free:** No agents (general knowledge only, limited)
- **Basic:** tax_documents, payroll, settings
- **Pro:** All agents

### 2.6 SessionManager - Agent State Persistence

**File:** `backend/app/agents/orchestration/session_manager.py`

**Responsibility:** Track which agent is currently active per thread

```python
class SessionManager:
    _active_agents: dict[str, str]  # thread_id → agent_key
    
    async def get_active_agent(thread_id) → str | None
    async def set_active_agent(thread_id, agent_key) → bool
    async def clear_active_agent(thread_id) → bool
```

**Usage Pattern:**
1. When handoff occurs → `set_active_agent(thread_id, "payroll_agent")`
2. Next message check → `get_active_agent(thread_id)` → returns payroll_agent
3. If supervisor handoff → `clear_active_agent(thread_id)` → returns to supervisor

**Storage:** In-memory dictionary (cleared when HandoffsManager cache cleared)

**Limitation:** Only persists within same orchestrator instance (thread cache scope)

---

## 3. AGENT DEFINITIONS

### 3.1 Supervisor Agent - Entry Point

**File:** `backend/app/agents/supervisor_agent.py`

**Model:** gpt-4o-mini (fast, efficient router)

**Responsibility:**
1. Analyze user intent
2. Route to specialized agent IMMEDIATELY
3. Never generate long responses (pure router)
4. Never access memory search or database tools

**Tools:**
- `show_subscription_upgrade()` - Widget to show upgrade prompt when blocked

**Guardrails:**
- `abuse_detection_guardrail` - Detects malicious input, prompt injection, off-topic

**Instructions:** Modular structure in `backend/app/agents/instructions/supervisor/`

### 3.2 Specialized Agents (7 Total)

All specialized agents follow the same pattern:

```python
def create_*_agent(db, openai_client, vector_store_ids=None) -> Agent:
    tools = [
        # Domain-specific tools
        # Widget tools (show_f29_detail_widget, etc.)
        # Memory tools (search_user_memory, search_company_memory)
        # FileSearchTool (if vector stores available)
    ]
    
    return Agent(
        name="*_agent",
        model=SPECIALIZED_MODEL,  # gpt-4.1-mini or gpt-5-nano
        instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{INSTRUCTIONS}",
        tools=tools,
    )
```

**The 7 Agents:**

| Agent | File | Purpose | Tools |
|-------|------|---------|-------|
| **General Knowledge** | `general_knowledge_agent.py` | Tax concepts, theory, definitions | F29 widgets, memory search, FileSearchTool |
| **Tax Documents** | `tax_documents_agent.py` | Real document data (invoices, receipts) | Document search, F29 widgets, memory |
| **Monthly Taxes** | `monthly_taxes_agent.py` | F29 form expertise | F29 widgets, memory |
| **Payroll** | `payroll_agent.py` | Labor law, employee management | Payroll tools, widgets |
| **Settings** | `settings_agent.py` | User preferences, notifications | Notification tools |
| **Expense** | `expense_agent.py` | Manual expense entry, OCR | Expense tools |
| **Feedback** | `feedback_agent.py` | Bug reports, feature requests | Feedback collection |

### 3.3 Agent Context Loading

**File:** `backend/app/agents/core/context_loader.py`

**Function:** `load_company_info()` and `format_company_context()`

**Automatic Company Data Loading:**
```python
async def load_company_info(db, company_id, use_cache=True):
    # Fetches from cache first (30-minute TTL)
    # Otherwise queries Company + CompanyTaxInfo tables
    
    return {
        "company": {
            "id": str(uuid),
            "rut": "76.123.456-7",
            "business_name": "Mi Empresa S.A.",
            "tax_regime": "Régimen General",
            "tax_info": {...}
        }
    }
```

**Formatting:** Converts to XML context for agent:
```xml
<company_info>
Fecha actual: Miércoles 13 de Noviembre de 2025

RUT: 76.123.456-7
Razón Social: Mi Empresa S.A.
Régimen Tributario: Régimen General
...
</company_info>
```

**Caching:** 30-minute TTL, in-memory cache
- Cache key: `str(company_id)`
- Expiry checked on each access
- Can be disabled with `use_cache=False`

---

## 4. TOOLS SYSTEM

### 4.1 Agent Tools Organization

**Location:** `backend/app/agents/tools/`

**Structure:**
```
tools/
├── tax/                      # Tax-specific tools
│   ├── documentos_tributarios_tools.py
│   ├── f29_tools.py
│   ├── remuneraciones_tools.py
│   ├── operacion_renta_tools.py
│   ├── sii_general_tools.py
│   └── expense_tools.py
├── payroll/
│   └── payroll_tools.py
├── settings/
│   └── notification_tools.py
├── feedback/
│   └── feedback_tools.py
├── memory/
│   └── memory_tools.py
├── widgets/                  # Widget builder tools
│   ├── tax_widget_tools.py
│   ├── payroll_widget_tools.py
│   ├── subscription_widget_tools.py
│   └── builders/
└── decorators.py             # Tool decoration utilities
```

### 4.2 Function Tools (Agent Tools)

**Pattern:** Using OpenAI Agents SDK `@function_tool` decorator

**Example:**
```python
from chatkit import function_tool

@function_tool
async def get_documents(
    context: FizkoContext,
    start_date: str,
    end_date: str,
    doc_type: str | None = None,
    company_id: UUID | None = None
) -> dict:
    """Get tax documents with flexible filtering."""
    # Implementation accesses context.request_context for DB access
    # Returns structured data
```

**Key Characteristics:**
- First parameter is always `FizkoContext` (agent framework convention)
- Async functions
- Type hints for all parameters
- Docstring describes behavior and examples
- Returns structured data (dict, list, etc.)

### 4.3 Widget Tools

**Location:** `backend/app/agents/tools/widgets/`

**Pattern:** Higher-level tools that construct ChatKit widgets

**Components:**
- `tax_widget_tools.py` - F29, tax summary widgets
- `payroll_widget_tools.py` - Payroll views
- `subscription_widget_tools.py` - Upgrade prompts
- `builders/` - Widget builders (f29_summary, tax_calculation, etc.)

**Example Usage:**
```python
show_f29_summary_widget,    # Available to all agents
show_f29_detail_widget,     # Shows detailed F29 breakdown
show_subscription_upgrade,  # Only supervisor uses when blocked
```

### 4.4 Memory Tools (Dual System)

**Location:** `backend/app/agents/tools/memory/memory_tools.py`

**Two separate search functions:**
1. `search_user_memory()` - Personal user preferences, history
2. `search_company_memory()` - Company-wide knowledge, settings

**Purpose:** Store agent-relevant context without full memory search

**Integration:** Added to most agents for context enrichment

---

## 5. UI TOOLS SYSTEM (ChatKit-Specific)

### 5.1 Purpose and Architecture

**Problem:** When user clicks a UI component (e.g., "View Contact"), agent needs context about that contact BEFORE processing

**Solution:** UI Tools pre-fetch and format component-specific data

**Flow:**
```
Frontend sends ui_component="contact_card"
    ↓
UIToolDispatcher.dispatch(ui_component="contact_card", ...)
    ↓
UIToolRegistry.get_tool("contact_card")
    ↓
ContactCardTool.process(UIToolContext)
    ↓
Returns UIToolResult with:
    - context_text (prepended to agent instructions)
    - structured_data (accessible to agent)
    - widget (optional immediate rendering)
    - agent_instructions (override instructions)
```

### 5.2 BaseUITool Interface

**File:** `backend/app/agents/ui_tools/core/base.py`

```python
class BaseUITool(ABC):
    @property
    @abstractmethod
    def component_name(self) -> str:
        """Name of UI component: "contact_card", "tax_summary_iva", etc."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description"""
        pass
    
    @property
    def domain(self) -> str:
        """Domain category: "contacts", "financials", etc."""
        return "general"
    
    @property
    def agent_instructions(self) -> str:
        """Optional component-specific agent instructions"""
        return ""
    
    @abstractmethod
    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process the UI interaction"""
        pass
```

**UIToolContext:**
- `ui_component`: Component name from frontend
- `user_message`: User's message
- `company_id`, `user_id`: Request context
- `db`: AsyncSession for data fetching
- `additional_data`: Extra context dict

**UIToolResult:**
- `success`: bool
- `context_text`: Prepended to agent instructions
- `structured_data`: Dict accessible to agent
- `metadata`: Processing metadata
- `error`: Error message if failed
- `widget`: Optional ChatKit widget to render
- `widget_copy_text`: Fallback text for widget

### 5.3 UI Tool Registry and Dispatcher

**File:** `backend/app/agents/ui_tools/core/registry.py` and `dispatcher.py`

**Registry Pattern:**
```python
@ui_tool_registry.register
class ContactCardTool(BaseUITool):
    @property
    def component_name(self) -> str:
        return "contact_card"
```

**Dispatcher:**
```python
result = await UIToolDispatcher.dispatch(
    ui_component="contact_card",
    user_message="Tell me about this contact",
    company_id=...,
    db=...,
)
```

### 5.4 Registered UI Tools

**Current Tools:**
- `contact_card` - Contact information display
- `tax_summary_iva` - IVA summary
- `tax_summary_revenue` - Revenue summary
- `tax_summary_expenses` - Expense summary
- `document_detail` - Document details
- `person_detail` - Employee/person details
- `f29_form_card` - F29 form display
- `pay_latest_f29` - F29 payment flow
- `add_employee_button` - Add employee flow
- `notification_generic` - Generic notification
- `notification_calendar_event` - Calendar event notification
- `tax_calendar_event` - Tax event calendar

**Note:** Tools must be imported in `__init__.py` to register (trigger @register decorator)

---

## 6. CONTEXT & STATE MANAGEMENT

### 6.1 FizkoContext - Agent-Specific Context

**File:** `backend/app/agents/core/context.py`

```python
class FizkoContext(AgentContext[dict[str, Any]]):
    """Extends ChatKit's AgentContext"""
    
    current_agent_type: str = "sii_general"
    thread_item_converter: Any | None = None
    company_info: dict[str, Any] | None = None
```

**Inheritance from ChatKit:**
- `thread`: Current ChatKit thread metadata
- `store`: Conversation store
- `request_context`: Request-specific data (user_id, user, etc.)

**Extended by Fizko:**
- `current_agent_type`: Tracks which agent type is active
- `thread_item_converter`: Attachment converter
- `company_info`: Preloaded company information

**Populated by:**
1. Runner context building
2. Company info loader (auto-loads on context creation)
3. UI tools (add context_text to instructions)
4. Guardrails (add guardrail results)

### 6.2 Attachment Stores

**Two implementations:**

**1. MemoryAttachmentStore** (for development/single-instance)
- **File:** `backend/app/agents/core/memory_attachment_store.py`
- In-memory storage of attachment content
- Fast but not shared across instances

**2. SupabaseAttachmentStore** (for production)
- **File:** `backend/app/agents/core/supabase_attachment_store.py`
- Stores attachments in Supabase Storage
- Shared across instances

**Responsibilities:**
- Store attachment metadata (name, mime_type, etc.)
- Store attachment content (base64 or binary)
- Track OpenAI vector_store_id (for FileSearchTool)
- Support retrieval by attachment_id

**Usage in Chat:**
```python
async def _convert_attachments_to_content(item, attachment_store):
    # Images: convert to base64 data URLs
    # PDFs: reference vector_store if available
```

---

## 7. SECURITY & GUARDRAILS

### 7.1 Subscription-Based Access Control

**Mechanism:** Multi-layer validation

**Layer 1 - Orchestration Level:**
```
SubscriptionValidator.get_available_agents(company_id)
    ↓ (queries subscription)
    → Returns: ["tax_documents_agent", "payroll_agent", ...]
```

**Layer 2 - Handoff Level:**
```
HandoffFactory.create_validated_handoff()
    ↓ (checks agent_key in agents dict)
    → If missing: return block_response
```

**Layer 3 - Agent Level:**
```
Supervisor has show_subscription_upgrade() tool
    → When handoff blocked, calls tool to show upgrade widget
```

### 7.2 Guardrails System

**File:** `backend/app/agents/guardrails/`

**Architecture:**
- Input guardrails: Validate user input before agent execution
- Output guardrails: Validate agent response
- Execute in parallel using asyncio
- Raise exceptions if tripwire triggered

**Current Guardrails:**
1. **Abuse Detection** (`implementations/abuse_detection.py`)
   - Detects malicious intent
   - Prompt injection detection
   - Off-topic request detection
   - Tripwire: Raises `InputGuardrailTripwireTriggered`

2. **PII Detection** (`implementations/pii_detection.py`)
   - Detects personally identifiable information
   - Pattern matching for common PII types

3. **Subscription Check** (`implementations/subscription_check.py`)
   - Validates agent access
   - Rate limiting

### 7.3 Row-Level Security (RLS)

**Implemented at Supabase level** (outside agent system)

**Example:** Only agents can query company data for their own company
```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Companies can view own documents"
ON documents FOR SELECT
USING (company_id = auth.jwt()->>'company_id'::uuid);
```

---

## 8. MULTI-CHANNEL SUPPORT

### 8.1 Channel Abstraction

**Supported Channels:**
1. **ChatKit (Web)** - Rich UI, widgets, streaming
2. **WhatsApp** - Text-only, no markdown, limited formatting

**Implementation:**
- `channel: str` parameter passed through orchestration
- Agents receive channel info in context
- Instructions may vary by channel
- Widget rendering only on web

### 8.2 Response Formatting Per Channel

**ChatKit:**
- Full widget support
- Streaming enabled
- Markdown formatting
- Multiple attachment types

**WhatsApp:**
- Plain text only
- No markdown
- No widgets
- Limited formatting (use Unicode, emojis)

**Handled in:** Channel-specific routers and services

---

## 9. EXECUTION FLOW (Detailed)

### 9.1 Request → Response Flow

```
1. ChatKit POST /chatkit/messages or WhatsApp webhook
   ↓ Authenticate user
   ↓ Extract company_id from subscription
   
2. Optional: UI Tool Processing
   await UIToolDispatcher.dispatch(
       ui_component=request.ui_component,
       user_message=request.message,
       company_id=company_id,
       db=db
   )
   ↓ Returns context_text to prepend
   
3. Guardrail Validation (Input)
   GuardrailRunner.run_input_guardrails()
   ↓ May raise exception if abuse detected
   
4. Agent Orchestration
   supervisor = handoffs_manager.get_supervisor_agent(
       thread_id=request.thread_id,
       db=db,
       company_id=company_id,
       channel=channel
   )
   ↓ Creates/returns cached orchestrator
   
5. Context Building
   context = FizkoContext(...)
   context.company_info = load_company_info(db, company_id)
   ↓ Populates context
   
6. Agent Execution
   result = await Runner.run(
       supervisor,
       user_input,
       context=context,
       session=session,
       max_turns=10
   )
   ↓ Supervisor → Handoff → Specialized agent
   ↓ Specialized agent uses tools → response
   
7. Output Guardrails (if implemented)
   GuardrailRunner.run_output_guardrails(response)
   
8. Format Response for Channel
   - ChatKit: Include widgets, streaming, markdown
   - WhatsApp: Plain text, no formatting
   
9. Return to User
   Response with message + metadata
```

### 9.2 Handoff Sequence

```
User: "Tell me about my employees"
    ↓
Supervisor.run()
    ↓ Analyzes intent: "payroll" domain
    ↓ Calls handoff: payroll_agent (tool call)
    ↓
PayrollAgent.run()
    ├─→ Executes: get_employees()
    ├─→ Executes: show_payroll_widget()
    └─→ Returns: Formatted response with data
    ↓
[Optional] Handoff back to supervisor
    (disabled by default to prevent disruption)
```

### 9.3 Subscription Check During Handoff

```
Supervisor wants to handoff to payroll_agent
    ↓
HandoffFactory.create_validated_handoff()
    ↓ on_handoff callback
    ├─→ Check: "payroll_agent" in self.agents
    │   └─→ If missing: return block_response
    │       "Payroll features require Pro plan"
    └─→ If present: Allow handoff
        ├─→ Update SessionManager
        ├─→ Log handoff event
        └─→ Execute agent
```

---

## 10. DATA FLOWS

### 10.1 Company Information Loading

```
Agent needs company data
    ↓
FizkoContext initialization
    ↓
context_loader.load_company_info(db, company_id)
    ↓ Check 30-min cache
    │   ├─→ HIT: Return cached data
    │   └─→ MISS: Query database
    ↓
SELECT Company, CompanyTaxInfo
    ↓
Format as XML context
    ↓
Inject into agent instructions
```

**Performance:** Cache hit ~0.003s, miss ~0.05s

### 10.2 Tool Execution Data Flow

```
Agent calls: get_documents(
    company_id=uuid,
    start_date="2025-10-01",
    end_date="2025-10-31"
)
    ↓
Tool receives:
    - context: FizkoContext with company_info
    - parameters from agent
    ↓
Tool executes database query
    └─→ AccessControl: WHERE company_id = company_id
    
Tool returns: dict with results
    ├─→ status: "success"
    ├─→ data: [documents...]
    └─→ count: number
    ↓
Agent processes response
    ├─→ Formats for user
    └─→ May call additional tools
```

### 10.3 UI Tool Data Flow

```
Frontend sends:
{
    "message": "Tell me about this contact",
    "ui_component": "contact_card",
    "additional_data": { "contact_id": "uuid" }
}
    ↓
Backend: UIToolDispatcher.dispatch()
    ├─→ Lookup tool by name
    ├─→ Create UIToolContext
    └─→ Execute tool.process(context)
        └─→ Fetch contact data from DB
        └─→ Format as context_text
        └─→ Return UIToolResult
    ↓
Result injected into agent:
    - context_text prepended to instructions
    - structured_data available as context
    - agent_instructions override (if any)
    ↓
Agent processes with enriched context
```

---

## 11. CONFIGURATION & CONSTANTS

### 11.1 Model Configuration

**File:** `backend/app/config/constants.py`

```python
SUPERVISOR_MODEL = "gpt-4o-mini"      # Fast router
SPECIALIZED_MODEL = "gpt-4.1-mini"    # Or gpt-5-nano for reasoning
REASONING_EFFORT = "low"              # For gpt-5 models
```

### 11.2 Subscription Scopes

**File:** `backend/app/agents/config/scopes.py`

```python
AGENT_SCOPES = {
    "free": {
        "agents": [],  # Limited general knowledge only
        "limitations": ["No document access", ...]
    },
    "basic": {
        "agents": ["tax_documents", "payroll", "settings"],
        "limitations": [...]
    },
    "pro": {
        "agents": ["all agents"],
        "limitations": []
    }
}
```

### 11.3 Agent Instructions

**Location:** `backend/app/agents/instructions/{agent_name}/`

**Structure:** Modular numbered markdown files
- `0_core.md` - Core instructions
- `1_context.md` - Context handling
- `2_tools.md` - Tool usage
- `3_examples.md` - Examples
- etc.

**Loading:** Combined by `instructions/__init__.py` using glob

---

## 12. DESIGN PATTERNS USED

### 12.1 Patterns Identified

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Singleton** | HandoffsManager, UIToolRegistry | Global instances |
| **Factory Method** | AgentFactory, HandoffFactory | Conditional creation |
| **Observer** | SessionManager, GuardrailRunner | Event tracking |
| **Strategy** | UI Tools, Attachment stores | Interchangeable implementations |
| **Lazy Initialization** | HandoffsManager.get_orchestrator() | Defer creation until needed |
| **Decorator** | @function_tool, @ui_tool_registry.register | Metadata attachment |
| **Dependency Injection** | Agent creation, context building | Loose coupling |
| **Template Method** | BaseUITool.process() | Subclass customization |

### 12.2 Architectural Principles

1. **Separation of Concerns**
   - Orchestration (HandoffsManager) separate from execution (Runner)
   - UI tools separate from agents
   - Guardrails separate from execution

2. **Single Responsibility**
   - Each agent: one domain
   - Each tool: one function
   - Each service: one job

3. **Open/Closed**
   - New agents can be added by subclassing
   - New tools can be added by @function_tool
   - New UI tools can be added by @ui_tool_registry.register

4. **Interface Segregation**
   - BaseUITool interface is minimal
   - Agent interface (from SDK) is well-defined
   - Tools use structured I/O

---

## 13. POTENTIAL ISSUES & IMPROVEMENT OPPORTUNITIES

### 13.1 Critical Issues

**Issue 1: Orchestrator Cache Unbounded Growth**
- **Problem:** HandoffsManager._orchestrator_cache has no size limit
- **Impact:** Memory leak if many threads created
- **Solution:** Implement LRU cache with max size
  ```python
  from functools import lru_cache
  # Or use: from cachetools import TTLCache
  _orchestrator_cache = TTLCache(maxsize=1000, ttl=3600)
  ```

**Issue 2: SessionManager Not Persistent**
- **Problem:** Active agent state lost if orchestrator cache cleared
- **Impact:** Multi-instance deployments lose handoff state
- **Solution:** Persist to Redis or Supabase
  ```python
  # In SessionManager
  async def set_active_agent(self, thread_id, agent_key):
      await redis.set(f"active_agent:{thread_id}", agent_key, ex=3600)
  ```

**Issue 3: Company Info Cache Key Collision**
- **Problem:** Cache key is just `str(company_id)`, no thread isolation
- **Impact:** Multiple threads access same cache (OK) but stale data possible
- **Solution:** Add expiry checking already done, no change needed

### 13.2 Design Improvements

**Improvement 1: Reduce Orchestrator Creation Time**
- **Current:** ~0.5s for full orchestrator creation
- **Suggestion:** 
  - Cache agent factory (don't recreate agents each time)
  - Pre-create supervisor separately
  - Use agent pooling

**Improvement 2: Simplify Handoff Configuration**
- **Current:** Handoffs need explicit config + agent availability check
- **Suggestion:**
  - Auto-generate handoff configs from agent list
  - Eliminate dual checks (factory + handoff factory)

**Improvement 3: Unified Memory System**
- **Current:** Separate user_memory and company_memory tools
- **Suggestion:**
  - Single memory search with scope parameter
  - Reduce tool count per agent

**Improvement 4: Better UI Tool Agent Instructions**
- **Current:** Instructions optional, stored in tool
- **Suggestion:**
  - Build instruction templates in core
  - Allow placeholders for context variables
  - Validate instructions against agent model

**Improvement 5: Subscription Validation Caching**
- **Current:** Calls guard on each orchestrator creation
- **Suggestion:**
  - Cache subscription checks with TTL
  - Invalidate on subscription change events

### 13.3 Testing Gaps

**Areas Not Heavily Tested:**
1. Handoff chains (A → B → C → A)
2. Subscription blocking with multiple agents
3. UI tool context injection correctness
4. Guardrail tripwire exception handling
5. Multi-instance synchronization
6. Channel-specific response formatting
7. Attachment store failover (memory → Supabase)

### 13.4 Documentation Gaps

**Missing Documentation:**
1. How to add a new specialized agent
2. How to add a new tool to an agent
3. How to add a new UI tool
4. UI component → UI tool mapping
5. Guardrail implementation guide
6. Channel-specific response formatting

---

## 14. EXTENSION POINTS

### 14.1 Adding a New Specialized Agent

**Steps:**
1. Create `backend/app/agents/specialized/new_agent.py`
   ```python
   def create_new_agent(db, openai_client, ...) -> Agent:
       return Agent(
           name="new_agent",
           model=SPECIALIZED_MODEL,
           instructions=NEW_AGENT_INSTRUCTIONS,
           tools=[...]
       )
   ```

2. Add to `specialized/__init__.py`
   ```python
   from .new_agent import create_new_agent
   __all__ = [..., "create_new_agent"]
   ```

3. Update `AgentFactory.create_available_agents()`
   ```python
   if "new_agent_name" in available_agent_names:
       agents["new_agent"] = create_new_agent(...)
   ```

4. Add to `HandoffFactory.get_standard_configs()`
   ```python
   HandoffConfig(
       agent_name="new_agent_name",
       agent_key="new_agent",
       ...
   )
   ```

5. Update subscription scopes if needed

### 14.2 Adding a New Tool to an Agent

**Steps:**
1. Create tool in `tools/{domain}/new_tool.py`
   ```python
   @function_tool
   async def my_tool(context: FizkoContext, ...) -> dict:
       ...
   ```

2. Import in agent definition
   ```python
   from ..tools.domain.new_tool import my_tool
   tools = [..., my_tool]
   ```

### 14.3 Adding a New UI Tool

**Steps:**
1. Create `ui_tools/tools/new_component.py`
   ```python
   @ui_tool_registry.register
   class NewComponentTool(BaseUITool):
       @property
       def component_name(self) -> str:
           return "new_component"
       
       async def process(self, context: UIToolContext):
           # Fetch data, format context
   ```

2. Import in `ui_tools/__init__.py` (triggers registration)
   ```python
   from .tools import NewComponentTool
   __all__ = [..., "NewComponentTool"]
   ```

### 14.4 Adding a New Channel

**Steps:**
1. Create channel handler (e.g., `routers/telegram/webhooks.py`)
2. Implement `AgentExecutionRequest` adapter
3. Call `agentRunner.execute(request, db)`
4. Handle response formatting for channel

---

## 15. SUMMARY TABLE

| Component | File | Responsibility | Key Method |
|-----------|------|-----------------|-----------|
| **HandoffsManager** | `orchestration/handoffs_manager.py` | Orchestrator caching, entry point | `get_supervisor_agent()` |
| **MultiAgentOrchestrator** | `orchestration/multi_agent_orchestrator.py` | Agent coordination, handoff config | `_initialize_agents()` |
| **AgentFactory** | `orchestration/agent_factory.py` | Conditional agent creation | `create_available_agents()` |
| **HandoffFactory** | `orchestration/handoff_factory.py` | Handoff creation & validation | `create_validated_handoff()` |
| **SubscriptionValidator** | `orchestration/subscription_validator.py` | Access control | `get_available_agents()` |
| **SessionManager** | `orchestration/session_manager.py` | Active agent tracking | `set_active_agent()` |
| **FizkoContext** | `core/context.py` | Agent context | (extends ChatKit) |
| **ContextLoader** | `core/context_loader.py` | Company info loading | `load_company_info()` |
| **BaseUITool** | `ui_tools/core/base.py` | UI tool interface | `process()` |
| **UIToolDispatcher** | `ui_tools/core/dispatcher.py` | Route UI interactions | `dispatch()` |
| **UIToolRegistry** | `ui_tools/core/registry.py` | Tool registration | `register()` |
| **GuardrailRunner** | `guardrails/runner.py` | Execute guardrails | `run_input_guardrails()` |
| **SupabaseAttachmentStore** | `core/supabase_attachment_store.py` | Attachment persistence | `store_attachment()` |

---

## CONCLUSION

Fizko's multi-agent system is a well-architected, modular platform that effectively:

1. **Routes** user queries to specialized agents via a supervisor
2. **Controls** access through subscription tiers at multiple layers
3. **Manages** complex agent state through thread-scoped caching
4. **Enriches** context via UI tools and company info loaders
5. **Secures** input/output with guardrails
6. **Supports** multiple channels (web, WhatsApp, extensible)
7. **Integrates** tools from tax, payroll, and administrative domains

**Key Strengths:**
- Clean separation of concerns
- Extensible architecture for new agents/tools
- Subscription-aware at orchestration level
- Automatic company context loading
- UI component-driven context injection

**Key Areas for Improvement:**
- Cache management (unbounded growth)
- Persistence for multi-instance deployments
- Performance optimization (orchestrator creation)
- Documentation and testing coverage
