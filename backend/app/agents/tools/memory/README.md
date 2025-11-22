# Memory Tools - Dual Memory System

This module provides a dual memory system using Mem0 for long-term context storage:

## Overview

The system maintains **two separate memory spaces**:

1. **User Memory** - Personal preferences and information specific to each user
2. **Company Memory** - Shared knowledge and information across the entire company

## Architecture

### Memory Storage Strategy

- **User Memory**: Stored with `user_id` as the entity identifier
- **Company Memory**: Stored with **normalized RUT** (without hyphens) as the entity identifier (e.g., `"772049315"`)

Both memory types use Mem0's async client with the same underlying infrastructure but maintain complete separation.

**Why use RUT for company memory?**
- Portable across environments (same RUT in dev/staging/prod)
- Stable identifier (doesn't change with database migrations)
- Human-readable and debuggable
- Matches the entity_id used in bulk memory loading system

## Available Tools

### User Memory Tools

#### `search_user_memory(query: str, limit: int = 3) -> str`

Search through the user's personal memory and past conversations.

**Use cases:**
- Recall user's personal preferences (e.g., "prefers short answers")
- Personal decisions (e.g., "wants to file F29 monthly")
- Personal context from past conversations
- Information specific to THIS USER (not shared with company)

**Example:**
```python
# In an agent tool
result = await search_user_memory(context, "user's communication preference")
```

#### `save_user_memory(content: str) -> str`

Save important information to the user's personal long-term memory.

**Use cases:**
- Store user's personal preferences (e.g., "User prefers short, concise answers")
- Personal decisions (e.g., "User wants to receive reminders 3 days before deadlines")
- Personal context for future conversations
- Information specific to THIS USER (not company-wide)

**Example:**
```python
# In an agent tool
await save_user_memory(context, "User prefers short, concise answers")
```

### Company Memory Tools

#### `search_company_memory(query: str, limit: int = 3) -> str`

Search through the company's shared memory and knowledge base.

**Use cases:**
- Company's tax regime and settings (e.g., "Company is on ProPyme regime")
- Company policies and decisions (e.g., "Uses monthly IVA filing")
- Shared business context (e.g., "Company changed accountant in Q2 2024")
- Information that applies to ALL users in the company

**Example:**
```python
# In an agent tool
result = await search_company_memory(context, "company's tax regime")
```

#### `save_company_memory(content: str) -> str`

Save important information to the company's shared long-term memory.

**Use cases:**
- Store company's tax regime and settings (e.g., "Company is on ProPyme regime")
- Company policies (e.g., "Company files IVA monthly")
- Business context (e.g., "Company started operations in January 2023")
- Information that should be accessible to ALL users in the company

**Example:**
```python
# In an agent tool
await save_company_memory(context, "Company is on ProPyme regime")
```

## When to Use Each Memory Type

### Use User Memory When:
- Storing **personal preferences** (communication style, notification settings)
- Recording **user-specific decisions** (filing preferences, reminder timing)
- Saving **personal context** (user's role, responsibilities)
- Information is **not relevant** to other users in the company

### Use Company Memory When:
- Storing **company-wide settings** (tax regime, fiscal year)
- Recording **business policies** (IVA filing frequency, accounting methods)
- Saving **shared context** (business history, major events)
- Information should be **accessible to all users** in the company

## Implementation Details

### Context Requirements

Both memory tools require access to `FizkoContext`:

- **User Memory**: Uses `context.request_context.get("user_id")` to identify the user
- **Company Memory**: Uses `context.company_info.get("rut")` to identify the company (normalized RUT without hyphens)

### Error Handling

Both tools handle common errors gracefully:

- **400 Bad Request**: Returned when no memories exist yet (empty database)
- **Missing Context**: Company memory returns an error if `company_id` is not available
- **General Errors**: Logged with full traceback and returned as error messages

### Memory Format

Memories are returned as bullet-point formatted strings:

```
- Company is on ProPyme regime
- Uses monthly IVA filing
- Started operations in January 2023
```

## Agent Integration

### Agents with Both Memory Types

The following agents have access to both user and company memory:

- **General Knowledge Agent** - Can store/recall both personal preferences and company information
- **Tax Documents Agent** - Can remember user preferences and company tax settings
- **Payroll Agent** - Can store user preferences and company payroll policies

### Agents with Search-Only Access

- **Supervisor Agent** - Can search both memory types but cannot save (delegates to specialists)

### Adding Memory Tools to New Agents

```python
from app.agents.tools.memory import (
    search_user_memory,
    save_user_memory,
    search_company_memory,
    save_company_memory,
)

def create_my_agent(db: AsyncSession, openai_client: AsyncOpenAI) -> Agent:
    tools = [
        # Memory tools
        search_user_memory,
        save_user_memory,
        search_company_memory,
        save_company_memory,
        # ... other tools
    ]

    return Agent(
        name="my_agent",
        model=SPECIALIZED_MODEL,
        instructions="...",
        tools=tools,
    )
```

## Legacy Compatibility

The old `search_memory` and `save_memory` functions are still available for backward compatibility:

- `search_memory` - Defaults to searching user memory (with deprecation warning)
- `save_memory` - Defaults to saving to user memory (with deprecation warning)

**New code should use the explicit functions** (`search_user_memory`, `search_company_memory`, etc.) for clarity.

## Environment Setup

Requires `MEM0_API_KEY` environment variable to be set:

```bash
export MEM0_API_KEY="your-mem0-api-key"
```

## Examples

### Example 1: User Preference

```python
# User says: "Recuerda que prefiero respuestas cortas"
await save_user_memory(context, "User prefers short, concise answers")

# Later, in any conversation:
preferences = await search_user_memory(context, "user preferences")
# Returns: "- User prefers short, concise answers"
```

### Example 2: Company Setting

```python
# User says: "Nuestra empresa está en régimen ProPyme"
await save_company_memory(context, "Company is on ProPyme tax regime")

# Later, any user in the company can retrieve:
regime = await search_company_memory(context, "tax regime")
# Returns: "- Company is on ProPyme tax regime"
```

### Example 3: Mixed Context

```python
# Search both memories for comprehensive context
user_prefs = await search_user_memory(context, "filing preferences")
company_settings = await search_company_memory(context, "tax regime")

# Agent can now respond with full context:
# - User's personal filing preferences
# - Company's tax regime setting
```

## Best Practices

1. **Be Specific**: Save specific, actionable information rather than vague statements
2. **Use Clear Language**: Write memories in clear, declarative sentences
3. **Avoid Duplication**: Check if information already exists before saving
4. **Choose the Right Memory Type**: Consider who needs access to the information
5. **Format Consistently**: Use consistent phrasing for similar types of information

## Troubleshooting

### No Memories Found

If searches return "No relevant memories found", this could mean:
- The memory database is empty (first use)
- The query doesn't match any stored memories
- The context (user_id or company_id) is incorrect

### Company Memory Not Working

If company memory tools fail, check:
- `company_info` is present in `FizkoContext`
- `company_info` includes a valid `"rut"` field
- The user's session includes company context
- The company was properly loaded in the context loader

### Memory Not Persisting

Memories are stored in Mem0's cloud service. If they're not persisting:
- Verify `MEM0_API_KEY` is set correctly
- Check Mem0 service status
- Review application logs for API errors
