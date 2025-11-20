# FIZKO MULTI-AGENT SYSTEM - VISUAL DIAGRAMS

## 1. System Architecture Overview

```
                          ┌──────────────────┐
                          │  User Message    │
                          │  (ChatKit/WA)    │
                          └────────┬─────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          ┌──────────────────┐        ┌──────────────────┐
          │  UI Tools        │        │  Guardrails      │
          │  Dispatcher      │        │  (Input)         │
          └────────┬─────────┘        └────────┬─────────┘
                   │                           │
                   └──────────────┬────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   HandoffsManager       │
                    │   .get_supervisor_()    │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
    ┌──────────────────────┐      ┌──────────────────────┐
    │  Check Cache         │      │ Create if New        │
    │  (thread_id)         │      │ Orchestrator         │
    └────────┬─────────────┘      └──────────┬───────────┘
             │                               │
             ▼                               ▼
    ┌──────────────────────┐      ┌──────────────────────┐
    │  Return Cached       │      │ Subscription Check   │
    │  Orchestrator        │      │ (Agent Access)       │
    └────────┬─────────────┘      └──────────┬───────────┘
             │                               │
             │                ┌──────────────┴──────────────┐
             │                │                             │
             │                ▼                             ▼
             │         ┌──────────────┐         ┌───────────────────┐
             │         │ AgentFactory │         │ Subscription      │
             │         │ .create_()   │         │ Validator         │
             │         └──────┬───────┘         └─────────┬─────────┘
             │                │                          │
             │                └──────────────┬───────────┘
             │                               │
             │                ┌──────────────▼──────────────┐
             │                │  HandoffFactory            │
             │                │  .create_validated_()      │
             │                └──────────────┬──────────────┘
             │                               │
             └───────────────────┬───────────┘
                                 │
                    ┌────────────▼───────────┐
                    │ MultiAgentOrchestrator │
                    │ (cached per thread_id) │
                    └────────────┬───────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
        ┌─────────────────┐           ┌──────────────────┐
        │ Supervisor Ag   │           │ Available Agents │
        │ (gpt-4o-mini)   │           │ (filtered by     │
        │                 │           │  subscription)   │
        │ Tools:          │           │                  │
        │ - Handoffs      │           │ - general_know   │
        │ - Subscription  │           │ - tax_docs       │
        │ - (widgets)     │           │ - payroll        │
        └────────┬────────┘           │ - monthly_taxes  │
                 │                    │ - settings       │
                 │                    │ - expense        │
                 │                    │ - feedback       │
                 │                    └──────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │  Runner.run()           │
        │  - Executes supervisor  │
        │  - Analyzes intent      │
        │  - Calls handoff tool   │
        │  - Transfers to spec.   │
        └────────┬────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │ Specialized Agent Runs  │
        │ - Calls tools           │
        │ - Returns response      │
        │ (optional: handoff back)│
        └────────┬────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │ Format for Channel      │
        │ - ChatKit: full widgets │
        │ - WhatsApp: plain text  │
        └────────┬────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │ Response to User        │
        └─────────────────────────┘
```

## 2. Agent Hierarchy and Handoffs

```
                    ┌─────────────────────────┐
                    │   SUPERVISOR AGENT      │
                    │   (gpt-4o-mini)         │
                    │                         │
                    │ Entry Point             │
                    │ Routes to specialists   │
                    └────────┬────────────────┘
                             │
        ┌────────┬──────────┬┼───┬───────┬─────┐
        │        │          ││   │       │     │
        ▼        ▼          ▼▼   ▼       ▼     ▼
    ┌────┐  ┌────┐  ┌────┐ ┌────┐  ┌───┐  ┌───┐  ┌────┐
    │🧠  │  │📄  │  │📋 │ │💼 │  │⚙️ │  │💰│  │💬 │
    │GEN │  │TAX │  │F29│ │PAY│  │SET│  │EXP│  │FBK│
    │    │  │DOC │  │   │ │ROLL
   │ ───┘  └────┘  └────┘ └────┘  └───┘  └───┘  └────┘
    │
    └─ Optional: Return to supervisor (disabled by default)
```

**Legend:**
- GEN = General Knowledge
- TAX DOC = Tax Documents
- F29 = Monthly Taxes
- PAYROLL = Payroll
- SET = Settings
- EXP = Expense
- FBK = Feedback

## 3. Orchestration Component Relationship

```
┌─────────────────────────────────────────────────────────┐
│                    HandoffsManager                      │
│                   (Global Singleton)                    │
│                                                         │
│  _orchestrator_cache: dict[thread_id → Orchestrator]   │
│                                                         │
│  get_supervisor_agent(thread_id, db, company_id, ...)  │
│  ├─ Check cache                                        │
│  ├─ If miss: create new Orchestrator                   │
│  └─ Return supervisor from orchestrator                │
└──────────────────────┬──────────────────────────────────┘
                       │ creates/returns
                       ▼
┌─────────────────────────────────────────────────────────┐
│            MultiAgentOrchestrator                       │
│                                                         │
│  agents: dict[agent_key → Agent]                       │
│  session_manager: SessionManager                       │
│                                                         │
│  _initialize_agents():                                 │
│  ├─ AgentFactory.create_available_agents()             │
│  ├─ HandoffFactory.create_validated_handoff()          │
│  └─ Configure bidirectional handoffs                   │
└────┬───────────────┬──────────────────┬────────────────┘
     │               │                  │
     ▼               ▼                  ▼
┌──────────┐ ┌─────────────┐ ┌──────────────────┐
│  Agent   │ │   Handoff   │ │  Subscription    │
│ Factory  │ │  Factory    │ │  Validator       │
│          │ │             │ │                  │
│Creates   │ │Creates      │ │Maps subscription │
│agents    │ │validated    │ │to available      │
│based on  │ │handoffs     │ │agents            │
│available │ │with checks  │ │                  │
│list      │ │             │ │                  │
└──────────┘ └─────────────┘ └────────┬─────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │ Subscription     │
                             │ Guard            │
                             │                  │
                             │ Queries company  │
                             │ subscription     │
                             │ from Supabase    │
                             └──────────────────┘
```

## 4. UI Tools Data Flow

```
Frontend                              Backend

User clicks:                          UIToolDispatcher
"View Contact Card"                   .dispatch()
    │                                 │
    └─── ui_component=                │
         "contact_card" ──────────────→ UIToolRegistry
                                       .get_tool()
                                       │
                                       ▼
                            ┌────────────────────────┐
                            │  ContactCardTool       │
                            │                        │
                            │  .component_name =     │
                            │    "contact_card"      │
                            │                        │
                            │  .process(context) ──┐ │
                            │    ├─ Fetch data   │  │ │
                            │    ├─ Format text  │  │ │
                            │    └─ Build result │  │ │
                            └──────┬───────────┘   │ │
                                   │←──────────────┘ │
                                   │                │
                                   ▼                │
                            UIToolResult           │
                            - success: true        │
                            - context_text: "..."  │
                            - structured_data: {}  │
                                   │
                                   ├─────────────────────→ Agent
                                   │                      Instructions
                                   │                      (prepended)
                                   │
                                   └─────────────────────→ Agent
                                                          Structured Data
```

## 5. Company Information Loading Pipeline

```
FizkoContext Creation
    │
    ▼
load_company_info(db, company_id)
    │
    ├─ Check cache key: str(company_id)
    │  ├─ HIT: Check TTL
    │  │   ├─ Valid (< 30min): Return cached ✓
    │  │   └─ Expired: Delete from cache
    │  │
    │  └─ MISS: Query database
    │      │
    │      ├─ SELECT Company WHERE id = company_id
    │      │  └─ Get: rut, business_name, trade_name, etc.
    │      │
    │      ├─ SELECT CompanyTaxInfo WHERE company_id = company_id
    │      │  └─ Get: tax_regime, sii_activity, legal_rep, etc.
    │      │
    │      ├─ Cache result with timestamp
    │      │
    │      └─ Return company_data dict
    │
    ▼
format_company_context(company_info)
    │
    ├─ Build XML template
    ├─ Add current date (Chile timezone)
    ├─ Insert RUT, business names
    ├─ Add tax information
    │
    └─ Return XML string

    ▼
Inject into agent instructions:
<company_info>
Fecha actual: Miércoles 13 de Noviembre de 2025
RUT: 76.123.456-7
Razón Social: Mi Empresa S.A.
Régimen Tributario: Régimen General
...
</company_info>
```

## 6. Subscription Validation Flow

```
Request arrives with company_id
    │
    ▼
SubscriptionValidator.get_available_agents(company_id)
    │
    ├─ If no company_id: Allow all agents
    │
    └─ If company_id: Check subscription
       │
       ▼
    SubscriptionGuard.get_available_agents(company_id)
       │
       ├─ Query Supabase: SELECT subscription WHERE company_id = ?
       │
       ├─ Get plan_code (e.g., "basic", "pro")
       │
       ├─ Map to scope: get_scope_for_plan(plan_code)
       │  ├─ "basic" → ["tax_documents", "payroll", "settings"]
       │  └─ "pro" → [all agents]
       │
       └─ Return: ["tax_documents", "payroll", "settings"]
           │
           ▼
       AgentFactory.create_available_agents([...])
           │
           ├─ Always: supervisor_agent
           ├─ If "tax_documents" in list: tax_documents_agent
           ├─ If "payroll" in list: payroll_agent
           ├─ If "settings" in list: settings_agent
           └─ etc.
           │
           ▼
       Only allowed agents created
           │
           ▼
       Supervisor can only handoff to created agents
           │
           ├─ If user asks for payroll (allowed): Handoff succeeds
           └─ If user asks for payroll (blocked): Return block_response
```

## 7. Message Execution Sequence (Detailed)

```
Time  Component              Action
────────────────────────────────────────────────────────
 T0   ChatKit Router        Receive POST /chatkit/messages
      │                     └─ Extract: thread_id, company_id, message
      │
 T1   UIToolDispatcher      Dispatch ui_component (if present)
      │                     └─ Returns: context_text, structured_data
      │
 T2   GuardrailRunner       Run input guardrails
      │                     └─ Check: abuse, PII, etc.
      │
 T3   HandoffsManager       get_supervisor_agent(thread_id, ...)
      │                     └─ Check cache, create if needed
      │
 T4   SubscriptionValidator Check subscription
      │                     └─ Determine available_agents
      │
 T5   AgentFactory          Create agents
      │                     └─ Only create allowed agents
      │
 T6   MultiAgentOrchestrator Configure handoffs
      │                     └─ Create validated handoffs
      │
 T7   ContextLoader         load_company_info()
      │                     └─ Fetch/cache company data
      │
 T8   Runner                run(supervisor, input, context, ...)
      │                     └─ Execute supervisor
      │
 T9   Supervisor Agent      Analyze intent
      │                     └─ Call handoff tool
      │
T10   HandoffFactory        Validate handoff
      │                     └─ Check agent exists
      │
T11   Specialized Agent     Execute tools
      │                     └─ Query DB, call widgets, etc.
      │
T12   GuardrailRunner       Run output guardrails (if any)
      │                     └─ Validate response
      │
T13   ChannelFormatter      Format for channel
      │                     └─ ChatKit: widgets, WhatsApp: plain text
      │
T14   Response              Return to user
                            └─ Message + metadata
```

## 8. Tool Execution Architecture

```
┌─────────────────────────────────────────┐
│  Agent wants to call: get_documents()   │
└────────────────────┬────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   Tool Invocation      │
        │   with parameters:     │
        │   - start_date         │
        │   - end_date           │
        │   - company_id         │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Tool Execution        │
        │  @function_tool        │
        │  async def             │
        │  get_documents(...)    │
        │    │                   │
        │    ├─ context is       │
        │    │  FizkoContext     │
        │    │  (has company_info
        │    │   and request_ctx)│
        │    │                   │
        │    ├─ Extract DB from  │
        │    │  context          │
        │    │                   │
        │    ├─ Query:           │
        │    │  SELECT ...       │
        │    │  WHERE company_id │
        │    │        = company  │
        │    │    AND date       │
        │    │        BETWEEN    │
        │    │                   │
        │    ├─ Process results  │
        │    │                   │
        │    └─ Return dict      │
        │       {status, data}   │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Tool Result Handling  │
        │                        │
        │  Agent receives:       │
        │  {                     │
        │    "status": "ok",     │
        │    "data": [...],      │
        │    "count": 42         │
        │  }                     │
        │                        │
        │  Agent processes:      │
        │  - Format for user     │
        │  - Call more tools if  │
        │    needed              │
        │  - Build response      │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Response to User      │
        └────────────────────────┘
```

## 9. Guardrails Execution

```
Input Guardrails (parallel execution)

Agent Execution Starts
    │
    ├──────┬──────┬──────┬──────┐
    │      │      │      │      │
    ▼      ▼      ▼      ▼      ▼
  ┌────┐┌────┐┌────┐┌────┐
  │GR1 ││GR2 ││GR3 ││GR4 │
  │    ││    ││    ││    │
  │Abuse││PII ││Rate││Subs│
  │Detc ││Det ││Lim ││Chk │
  └──┬─┘└──┬─┘└──┬─┘└──┬─┘
     │     │     │     │
     └─────┼─────┼─────┘
           │
     All completed?
           │
        ┌──┴──┐
        │     │
      YES    NO
        │     │
        ▼     ▼
   Continue  Raise Exception
             (Tripwire)
```

## 10. Cache Architecture

```
┌────────────────────────────────────────────────────┐
│         HandoffsManager Orchestrator Cache         │
│                                                    │
│  _orchestrator_cache: {                            │
│    "thread_abc123": MultiAgentOrchestrator,        │
│    "thread_def456": MultiAgentOrchestrator,        │
│    "thread_ghi789": MultiAgentOrchestrator,        │
│    ...                                             │
│  }                                                 │
│                                                    │
│  Issues:                                           │
│  ✗ Unbounded growth (no TTL)                       │
│  ✗ Memory leak if many threads                     │
│                                                    │
│  Solution:                                         │
│  → Use TTLCache(maxsize=1000, ttl=3600)            │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│        Company Info Cache (In-Memory)              │
│                                                    │
│  _company_info_cache: {                            │
│    "uuid-1234": (timestamp, company_data),         │
│    "uuid-5678": (timestamp, company_data),         │
│    ...                                             │
│  }                                                 │
│                                                    │
│  TTL: 30 minutes                                   │
│                                                    │
│  Hit Rate: ~90% in production                      │
│  Cache Hit Time: ~3ms                              │
│  Cache Miss Time: ~50ms                            │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│         SessionManager (In-Memory)                 │
│                                                    │
│  _active_agents: {                                 │
│    "thread_abc": "payroll_agent",                  │
│    "thread_def": "tax_documents_agent",            │
│    ...                                             │
│  }                                                 │
│                                                    │
│  Issues:                                           │
│  ✗ Lost if orchestrator cache cleared              │
│  ✗ Not shared across instances                     │
│                                                    │
│  Solution for multi-instance:                      │
│  → Persist to Redis with TTL                       │
└────────────────────────────────────────────────────┘
```

---

This document provides visual representations of the key architectural components and data flows in the Fizko multi-agent system.
