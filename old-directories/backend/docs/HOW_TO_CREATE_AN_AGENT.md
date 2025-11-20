# How to Create a New Specialized Agent

This guide walks you through creating a new specialized agent in the Fizko multi-agent system, using the Expense Agent as a reference example.

## Table of Contents

1. [Overview](#overview)
2. [Step 1: Create Agent Instructions](#step-1-create-agent-instructions)
3. [Step 2: Create Agent Implementation](#step-2-create-agent-implementation)
4. [Step 3: Create Agent Tools](#step-3-create-agent-tools)
5. [Step 4: Register Agent in Orchestrator](#step-4-register-agent-in-orchestrator)
6. [Step 5: Update Supervisor Instructions](#step-5-update-supervisor-instructions)
7. [Step 6: Update Subscription System](#step-6-update-subscription-system)
8. [Step 7: Update Frontend (Optional)](#step-7-update-frontend-optional)
9. [Testing Your Agent](#testing-your-agent)
10. [Best Practices](#best-practices)

---

## Overview

The Fizko platform uses a **multi-agent architecture** with:
- **Supervisor Agent**: Routes queries to specialized agents
- **Specialized Agents**: Handle specific domains (tax, payroll, expenses, etc.)

Each agent has:
- **Instructions**: Markdown files defining behavior, scope, and workflows
- **Tools**: Functions the agent can call to access data or perform actions
- **Handoffs**: Configuration for routing between agents

**Architecture:**
```
User Query
    ↓
Supervisor Agent (gpt-4o-mini)
    ↓ (handoff)
Specialized Agent (gpt-4o-mini)
    ↓ (tool calls)
Database / External APIs
```

---

## Step 1: Create Agent Instructions

Agent instructions are modular markdown files that guide the agent's behavior.

### 1.1 Create Instruction Directory

```bash
mkdir -p backend/app/agents/instructions/your_agent_name
```

### 1.2 Create Instruction Files

Create **9 numbered markdown files** (following the standard structure):

```
backend/app/agents/instructions/your_agent_name/
├── 1_system_overview.md          # Role, personality, scope
├── 2_objectives_and_responsibilities.md  # Core duties
├── 3_context_and_data_sources.md # Available data and memory
├── 4_interaction_rules.md        # Conversation style and flow
├── 5_tool_usage_policy.md        # How to use tools
├── 6_reasoning_and_workflow.md   # Decision trees and workflows
├── 7_output_format.md            # Response templates
├── 8_error_and_fallback.md       # Error handling
└── 9_safety_and_limitations.md   # Privacy, compliance, boundaries
```

### 1.3 Example: System Overview

**`1_system_overview.md`:**
```markdown
You are the [Agent Name] of Fizko, a Chilean tax expert system.

Your primary function is to [primary responsibility].

## ROLE
- [Key responsibility 1]
- [Key responsibility 2]
- [Key responsibility 3]

## SCOPE
**You handle:**
- [Task type 1]
- [Task type 2]

**You DON'T handle:**
- [Out of scope 1] → [Other Agent] handles this
- [Out of scope 2] → [Other Agent] handles this

## PERSONALITY
- [Trait 1]: [Description]
- [Trait 2]: [Description]
- [Trait 3]: [Description]
```

### 1.4 Example: Workflow (Keep it Simple!)

**`6_reasoning_and_workflow.md`:**
```markdown
# REASONING AND WORKFLOW

## QUICK DECISION TREE

\```
User wants to [main action]?
├─ YES → Go to [MAIN WORKFLOW] (3 steps below)
└─ NO  → Is it a query?
          ├─ YES → Use [query_tool]()
          └─ NO  → Provide guidance or handoff
\```

## MAIN WORKFLOW (3 SIMPLE STEPS)

### STEP 1: [First Action]
\```
1. [Sub-action 1]
2. [Sub-action 2]
3. Confirm with user
\```

### STEP 2: [Second Action]
\```
1. [Sub-action 1]
2. [Sub-action 2]
\```

### STEP 3: [Final Action]
\```
Call [tool_name]() with:
- param1
- param2

Show confirmation:
"✅ [Success message]"
\```

### KEY RULES
1. **Rule 1** - [Description]
2. **Rule 2** - [Description]
3. **Rule 3** - [Description]
```

**Reference**: See `backend/app/agents/instructions/expense/` for a complete example.

### 1.5 Register Instructions

**`backend/app/agents/instructions/__init__.py`:**
```python
# Add your agent instructions
YOUR_AGENT_INSTRUCTIONS = _load_modular_instruction("your_agent_name")

__all__ = [
    # ... existing agents
    "YOUR_AGENT_INSTRUCTIONS",
]
```

---

## Step 2: Create Agent Implementation

### 2.1 Create Agent File

**`backend/app/agents/specialized/your_agent_name_agent.py`:**

```python
"""Your Agent Name - Specialized agent for [purpose]."""

from __future__ import annotations

from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SPECIALIZED_MODEL
from app.agents.instructions import YOUR_AGENT_INSTRUCTIONS
from ..tools.your_domain import (
    your_tool_1,
    your_tool_2,
)
from ..tools.memory import (
    search_user_memory,
    search_company_memory,
)

# Recommended prefix for all agents
RECOMMENDED_PROMPT_PREFIX = """
You are communicating in Spanish (Chile) with business users.
Be professional, clear, and helpful.
"""


def create_your_agent_name_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Your Agent Name specialized agent.

    This agent handles:
    - [Responsibility 1]
    - [Responsibility 2]
    - [Responsibility 3]

    Example queries:
    - "[Example query 1]"
    - "[Example query 2]"
    - "[Example query 3]"
    """

    tools = [
        # Your domain-specific tools
        your_tool_1,
        your_tool_2,

        # Memory tools (recommended for all agents)
        search_user_memory,     # User preferences
        search_company_memory,  # Company policies
    ]

    agent = Agent(
        name="your_agent_name_agent",
        model=SPECIALIZED_MODEL,  # gpt-4o-mini (fast and cheap)
        instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{YOUR_AGENT_INSTRUCTIONS}",
        tools=tools,
    )

    return agent
```

### 2.2 Register Agent

**`backend/app/agents/specialized/__init__.py`:**
```python
from .your_agent_name_agent import create_your_agent_name_agent

__all__ = [
    # ... existing agents
    "create_your_agent_name_agent",
]
```

---

## Step 3: Create Agent Tools

Tools are functions the agent calls to perform actions.

### 3.1 Create Tools Directory

```bash
mkdir -p backend/app/agents/tools/your_domain
```

### 3.2 Create Tool Implementation

**`backend/app/agents/tools/your_domain/your_tools.py`:**

```python
"""Tools for [your domain]."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from agents import function_tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.core import FizkoContext
from app.repositories.your_repository import YourRepository
from app.config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@function_tool
async def your_tool_name(
    context: FizkoContext,
    param1: str,
    param2: int,
    param3: str | None = None,
) -> dict[str, Any]:
    """
    [Brief description of what the tool does].

    Args:
        context: Fizko agent context (automatically injected)
        param1: [Description]
        param2: [Description]
        param3: [Optional description]

    Returns:
        Dictionary with results or error information

    Example:
        >>> result = await your_tool_name(context, "value1", 42)
        >>> print(result["data"])
    """
    try:
        # Validate inputs
        if not param1:
            return {
                "error": "param1 is required",
                "message": "Please provide param1"
            }

        # Get database session
        async with AsyncSessionLocal() as db:
            repo = YourRepository(db)

            # Perform action
            result = await repo.do_something(
                company_id=context.company_id,
                param1=param1,
                param2=param2,
            )

        # Return success
        return {
            "success": True,
            "data": result,
            "message": "Operation completed successfully"
        }

    except Exception as e:
        logger.error(f"Error in your_tool_name: {e}", exc_info=True)
        return {
            "error": "Operation failed",
            "message": str(e)
        }
```

### 3.3 Register Tools

**`backend/app/agents/tools/your_domain/__init__.py`:**
```python
"""Your domain tools."""

from .your_tools import (
    your_tool_name,
    another_tool,
)

__all__ = [
    "your_tool_name",
    "another_tool",
]
```

### 3.4 Tool Best Practices

1. **Always accept `FizkoContext` as first parameter** - Provides company_id, user_id, etc.
2. **Use descriptive docstrings** - Agent uses this to understand when to call the tool
3. **Return structured dictionaries** - Include `success`, `error`, `data`, `message` keys
4. **Handle errors gracefully** - Return error dict instead of raising exceptions
5. **Use absolute imports** - `from app.X import Y` instead of relative imports
6. **Log operations** - Use `logger.info()` for important actions

---

## Step 4: Register Agent in Orchestrator

The orchestrator manages all agents and their handoffs.

### 4.1 Import Your Agent

**`backend/app/agents/orchestration/multi_agent_orchestrator.py`:**

```python
from ..specialized import (
    # ... existing agents
    create_your_agent_name_agent,
)
```

### 4.2 Add to Agent List

Find the `_get_available_agents_for_company` method and add your agent:

```python
async def _get_available_agents_for_company(self) -> list[str]:
    if not self.company_id:
        return [
            "general_knowledge",
            "tax_documents",
            "f29",
            "payroll",
            "settings",
            "expense",
            "your_agent_name",  # ← Add here
        ]
    # ...
```

### 4.3 Initialize Agent

In the `_initialize_agents` method:

```python
if "your_agent_name" in self._available_agents:
    self.agents["your_agent_name_agent"] = create_your_agent_name_agent(
        db=self.db,
        openai_client=self.openai_client
    )
    logger.debug("✅ Created your_agent_name_agent")
```

### 4.4 Configure Supervisor Handoff

In the `_configure_supervisor_handoffs` method:

```python
# Your Agent Name
your_agent_handoff = create_handoff_with_check(
    agent_name="your_agent_name",
    agent_key="your_agent_name_agent",
    display_name="Your Agent Display Name",
    icon="🎯",  # Choose an appropriate emoji
    description=(
        "Transfer to Your Agent Name expert for [description]. "
        "Provide a brief reason for the transfer."
    ),
)
if your_agent_handoff:
    handoffs_list.append(your_agent_handoff)
```

### 4.5 Configure Bidirectional Handoff (Optional)

In the `_configure_bidirectional_handoffs` method:

```python
for agent_name in [
    "general_knowledge_agent",
    "tax_documents_agent",
    "payroll_agent",
    "settings_agent",
    "expense_agent",
    "your_agent_name_agent",  # ← Add here
]:
    # ... handoff configuration
```

### 4.6 Update Factory Function

At the bottom of the file:

```python
else:
    # No company_id: allow all agents (anonymous, testing)
    available_agents = [
        "general_knowledge",
        "tax_documents",
        "f29",
        "payroll",
        "settings",
        "expense",
        "your_agent_name",  # ← Add here
    ]
```

---

## Step 5: Update Supervisor Instructions

The supervisor needs to know when to route to your agent.

### 5.1 Add to Agent List

**`backend/app/agents/instructions/supervisor/3_context_and_data_sources.md`:**

```markdown
## AVAILABLE SPECIALIZED AGENTS

1. **General Knowledge Agent** - Tax concepts, definitions, regulations
2. **Tax Documents Agent** - Real document data, sales/purchases, DTEs
3. **Monthly Taxes Agent** - F29, IVA monthly declarations
4. **Payroll Agent** - Employee management, labor laws
5. **Settings Agent** - Company settings, preferences
6. **Expense Agent** - Manual expense registration, OCR
7. **Your Agent Name** - [Brief description of what it does]
```

### 5.2 Add Routing Rules

**`backend/app/agents/instructions/supervisor/5_tool_usage_policy.md`:**

```markdown
**→ Transfer to Your Agent Name** for:
- [Query type 1]
- [Query type 2]
- [Query type 3]
- "[Example query in Spanish]"
- NOTE: [Important distinction from other agents]
```

### 5.3 Update Decision Tree

**`backend/app/agents/instructions/supervisor/6_reasoning_and_workflow.md`:**

```markdown
## DECISION TREE

\```
User Query
    ↓
Search Memory (user + company)
    ↓
Analyze Query Type
    ↓
    ├─ Theoretical/Conceptual? → General Knowledge Agent
    ├─ DTE Data? → Tax Documents Agent
    ├─ F29 / Monthly Taxes? → Monthly Taxes Agent
    ├─ Manual Expense Registration? → Expense Agent
    ├─ [Your Query Type]? → Your Agent Name
    ├─ Payroll/Employees? → Payroll Agent
    └─ Settings/Configuration? → Settings Agent
\```
```

---

## Step 6: Update Subscription System

Control which subscription plans have access to your agent.

### 6.1 Add to Subscription Guard

**`backend/app/agents/core/subscription_guard.py`:**

```python
async def get_available_agents(self, company_id: UUID) -> list[str]:
    # All possible agents
    all_agents = [
        "general_knowledge",
        "tax_documents",
        "f29",
        "payroll",
        "settings",
        "expense",
        "your_agent_name",  # ← Add here
    ]
    # ...
```

### 6.2 Create Migration

**`backend/supabase/migrations/YYYYMMDDHHMMSS_add_your_agent_to_plans.sql`:**

```sql
-- Add Your Agent Name to subscription plans
-- Description of what your agent does and why it's in these plans

-- Free Plan - Add your_agent_name
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents,your_agent_name}',
    'true'::jsonb
)
WHERE code = 'free';

-- Basic Plan - Add your_agent_name
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents,your_agent_name}',
    'true'::jsonb
)
WHERE code = 'basic';

-- Pro Plan - Add your_agent_name
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents,your_agent_name}',
    'true'::jsonb
)
WHERE code = 'pro';
```

### 6.3 Apply Migration

Using Supabase MCP or SQL Editor:

```python
# Via MCP (in code)
await mcp__supabase_staging__apply_migration(
    name="add_your_agent_to_plans",
    query="[SQL from above]"
)
```

Or via Supabase SQL Editor:
1. Go to your Supabase project
2. Open SQL Editor
3. Paste migration SQL
4. Execute

---

## Step 7: Update Frontend (Optional)

Add a quick prompt button for your agent.

**`frontend/src/shared/lib/config.ts`:**

```typescript
export const STARTER_PROMPTS: StartScreenPrompt[] = [
  // ... existing prompts
  {
    label: "[Action user will take]",
    prompt: "[Full query to send to agent]",
    icon: "notebook-pencil",  // Choose appropriate icon
  },
];
```

---

## Testing Your Agent

### 8.1 Type Check

```bash
python3 -m py_compile backend/app/agents/specialized/your_agent_name_agent.py
python3 -m py_compile backend/app/agents/orchestration/multi_agent_orchestrator.py
python3 -m py_compile backend/app/agents/core/subscription_guard.py
```

### 8.2 Start Development Server

```bash
cd backend
./dev.sh  # Production parity (Gunicorn + 2 workers)
```

### 8.3 Test via Chat

1. Open frontend: `http://localhost:5173`
2. Type a query that should trigger your agent
3. Check logs to verify:
   - Agent is in available agents list
   - Supervisor hands off to your agent
   - Your agent calls the correct tools

**Look for log lines like:**
```
📋 Available agents for company X: ..., your_agent_name
🎯 → Your Agent Display Name | Reason: ... | Tools: N
```

### 8.4 Test Tool Execution

Trigger your agent to call a tool and verify:
- Tool executes successfully
- Returns expected data format
- Agent processes the response correctly
- User receives proper feedback

---

## Best Practices

### Architecture

1. **Single Responsibility** - Each agent should have one clear purpose
2. **Clear Boundaries** - Define what agent DOES and DOESN'T handle
3. **Smart Handoffs** - Guide users to the right agent when out of scope

### Instructions

1. **Keep it Simple** - Reduce 6-phase workflows to 3 simple steps
2. **Use Examples** - Show ❌ BAD vs ✅ GOOD patterns
3. **Decision Trees** - Visual flowcharts help agents reason
4. **Be Specific** - "Call create_expense()" not "register the data"

### Tools

1. **Descriptive Names** - `create_manual_expense` not `create_thing`
2. **Clear Docstrings** - Agent relies on this to know when to call
3. **Structured Returns** - Always return dicts with standard keys
4. **Handle Errors** - Return error dicts, don't raise exceptions
5. **Validate Inputs** - Check required params before processing

### Testing

1. **Test Edge Cases** - Missing params, invalid data, API errors
2. **Test Handoffs** - Verify supervisor routes correctly
3. **Test Subscriptions** - Verify blocked/allowed access
4. **Monitor Logs** - Watch for agent selection and tool calls

### Performance

1. **Use Caching** - Cache subscription checks, company data
2. **Async Everything** - All DB operations must be async
3. **Batch Operations** - When possible, batch multiple queries
4. **Timeout Handling** - Set reasonable timeouts for external APIs

---

## Checklist

Before marking your agent as complete:

- [ ] Created 9 instruction markdown files
- [ ] Created agent implementation file
- [ ] Created at least 2 tools for the agent
- [ ] Registered agent in orchestrator (5 locations)
- [ ] Updated supervisor instructions (3 files)
- [ ] Added to subscription guard
- [ ] Created and applied migration
- [ ] Added frontend quick prompt (optional)
- [ ] Type-checked all Python files
- [ ] Tested agent via chat interface
- [ ] Verified tool execution
- [ ] Verified subscription blocking works
- [ ] Reviewed logs for proper routing

---

## Reference Implementation

For a complete, working example, see:
- **Agent**: `backend/app/agents/specialized/expense_agent.py`
- **Instructions**: `backend/app/agents/instructions/expense/`
- **Tools**: `backend/app/agents/tools/tax/expense_tools.py`
- **Migration**: `backend/supabase/migrations/20251110192000_add_expense_agent_to_all_plans.sql`

---

## Need Help?

- **Architecture Questions**: See `backend/app/agents/README.md`
- **Tool Development**: See `backend/app/agents/tools/README.md`
- **Subscription System**: See `backend/docs/SUBSCRIPTION_SYSTEM.md`
- **Database Sessions**: See `backend/docs/DATABASE_SESSION_MANAGEMENT.md`

---

## Common Issues

### "Agent not in available agents list"
- Check subscription guard includes your agent
- Verify migration was applied to database
- Restart development server

### "Supervisor doesn't route to my agent"
- Check supervisor instructions include routing rules
- Verify agent name matches exactly in all places
- Look for typos in agent_name vs agent_key

### "Tool not found"
- Verify tool is imported in agent file
- Check tool is in agent's tools list
- Verify absolute imports (not relative)

### "Import errors"
- Use absolute imports: `from app.X import Y`
- Check __init__.py exports
- Verify circular import issues
