# UI Tools System Architecture

## 📐 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                                                                  │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │ ContactCard    │         │ TaxSummaryCard   │               │
│  │                │         │                  │               │
│  │ onClick() ─────┼────┬───►│ onClick() ───────┼───┐          │
│  └────────────────┘    │    └──────────────────┘   │          │
│                        │                            │          │
│         ChateableWrapper(uiComponent="contact_card")│          │
│                        │                            │          │
└────────────────────────┼────────────────────────────┼──────────┘
                         │                            │
                         │    POST /chatkit?         │
                         │    ui_component=...        │
                         ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ main.py (FastAPI)                                        │  │
│  │                                                           │  │
│  │  @app.post("/chatkit")                                   │  │
│  │  ┌─────────────────────────────────────────┐            │  │
│  │  │ 1. Extract ui_component from query      │            │  │
│  │  │ 2. Get DB session                       │            │  │
│  │  │ 3. Call UIToolDispatcher.dispatch()     │            │  │
│  │  └─────────────────┬───────────────────────┘            │  │
│  └────────────────────┼──────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ UIToolDispatcher                                         │  │
│  │                                                           │  │
│  │  dispatch(ui_component, user_message, company_id, db)    │  │
│  │  ┌────────────────────────────────────────┐             │  │
│  │  │ 1. Lookup tool in registry             │             │  │
│  │  │ 2. Create UIToolContext                │             │  │
│  │  │ 3. Call tool.process(context)          │             │  │
│  │  │ 4. Return UIToolResult                 │             │  │
│  │  └─────────────────┬──────────────────────┘             │  │
│  └────────────────────┼──────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ UI Tool Registry                                         │  │
│  │                                                           │  │
│  │  {                                                        │  │
│  │    "contact_card":      ContactCardTool,                 │  │
│  │    "tax_summary_card":  TaxSummaryCardTool,              │  │
│  │    ...                                                    │  │
│  │  }                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Specific UI Tool (e.g., ContactCardTool)                 │  │
│  │                                                           │  │
│  │  async def process(context: UIToolContext):              │  │
│  │    1. Validate context (db, company_id)                  │  │
│  │    2. Extract parameters from message                    │  │
│  │    3. Query database (contacts, transactions)            │  │
│  │    4. Format data into markdown                          │  │
│  │    5. Return UIToolResult                                │  │
│  │       - success: True                                    │  │
│  │       - context_text: "## 📇 CONTEXTO: ..."              │  │
│  │       - structured_data: {...}                           │  │
│  └─────────────────┬────────────────────────────────────────┘  │
│                    │                                             │
│                    │ UIToolResult                                │
│                    ▼                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ main.py                                                  │  │
│  │                                                           │  │
│  │  context = {                                             │  │
│  │    "ui_tool_result": result,                             │  │
│  │    "ui_context_text": result.context_text,  ◄────────┐   │  │
│  │    ...                                                │   │  │
│  │  }                                                    │   │  │
│  │  server.process(payload, context) ─────────┐         │   │  │
│  └────────────────────────────────────────────┼─────────┼───┘  │
│                                                │         │      │
│                                                ▼         │      │
│  ┌──────────────────────────────────────────────────────┼───┐  │
│  │ FizkoChatKitServer.respond()                         │   │  │
│  │                                                       │   │  │
│  │  context.get("ui_context_text") ──────────────────────┘   │  │
│  │  Prepend to user_message:                                │  │
│  │                                                           │  │
│  │  "## 📇 CONTEXTO: Información de Contacto\n\n            │  │
│  │   **Proveedor ABC**\n                                    │  │
│  │   RUT: 76555666-7\n                                      │  │
│  │   ...\n\n                                                 │  │
│  │   [User's original message]"                             │  │
│  │                                                           │  │
│  │  Runner.run_streamed(agent, enriched_message) ────┐     │  │
│  └───────────────────────────────────────────────────┼─────┘  │
│                                                       │        │
│                                                       ▼        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Unified Agent (Fizko)                                    │  │
│  │                                                           │  │
│  │  Receives enriched message with pre-loaded context       │  │
│  │  Can immediately answer without calling tools            │  │
│  │                                                           │  │
│  │  Response: "Según la información del contacto..."        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 🔄 Flow Sequence

1. **User clicks UI component** (Frontend)
   - User clicks on `ContactCard`
   - `ChateableWrapper` captures click
   - Generates message with `ui_component="contact_card"`

2. **Request sent to backend**
   ```
   POST /chatkit?company_id=xxx&ui_component=contact_card
   Body: { "op": "create_message", "text": "Tell me about this contact" }
   ```

3. **Main.py intercepts** (Backend entry)
   - Extracts `ui_component` from query params
   - Creates DB session
   - Calls `UIToolDispatcher.dispatch()`

4. **Dispatcher routes to tool** (Routing)
   - Looks up `"contact_card"` in registry
   - Finds `ContactCardTool`
   - Creates `UIToolContext` with all data
   - Calls `tool.process(context)`

5. **Tool fetches data** (Data loading)
   - `ContactCardTool.process()` runs
   - Queries database for contact info
   - Queries transaction history
   - Aggregates sales/purchase data

6. **Tool formats context** (Formatting)
   - Converts data to markdown
   - Creates human-readable sections
   - Returns `UIToolResult` with formatted text

7. **Context added to request** (Context injection)
   - `ui_context_text` added to request context
   - Passed to `FizkoChatKitServer`

8. **Agent receives enriched message** (Agent processing)
   - `ui_context_text` prepended to user message
   - Agent sees both context and user question
   - Agent can answer immediately without tools

9. **Response streamed back** (Response)
   - Agent generates response using context
   - Response streamed to frontend
   - User gets instant, contextual answer

## 📁 File Structure

```
backend/app/agents/ui_tools/
├── __init__.py              # Exports and imports
├── base.py                  # Base classes (BaseUITool, UIToolContext, UIToolResult)
├── registry.py              # UIToolRegistry - auto-registration
├── dispatcher.py            # UIToolDispatcher - routing logic
├── contact_card.py          # ContactCardTool implementation
├── tax_summary_card.py      # TaxSummaryCardTool implementation
├── _template.py             # Template for new tools
├── test_ui_tools.py         # Test suite
├── README.md                # Developer documentation
└── ARCHITECTURE.md          # This file
```

## 🧩 Key Components

### 1. BaseUITool (base.py)
Abstract base class that all UI tools inherit from.

**Key methods:**
- `component_name` - Must match frontend parameter
- `description` - Human-readable description
- `domain` - Categorization (contacts, financials, etc.)
- `process(context)` - Main processing logic

### 2. UIToolRegistry (registry.py)
Manages tool registration and lookup.

**Key features:**
- Auto-registration via `@ui_tool_registry.register` decorator
- Tool lookup by component name
- List all registered tools
- Domain-based filtering

### 3. UIToolDispatcher (dispatcher.py)
Routes UI component interactions to appropriate tools.

**Key features:**
- Validates ui_component parameter
- Creates UIToolContext
- Handles errors gracefully
- Falls back to legacy system if tool fails

### 4. UIToolContext (base.py)
Data structure passed to tools containing:
- `ui_component` - Component name
- `user_message` - User's message
- `company_id` - Current company
- `user_id` - Current user
- `db` - Database session
- `additional_data` - Extra context

### 5. UIToolResult (base.py)
Return type from tools containing:
- `success` - Whether processing succeeded
- `context_text` - Formatted markdown for agent
- `structured_data` - Raw data (for potential tool access)
- `metadata` - Additional info for logging
- `error` - Error message if failed

## 🎯 Design Patterns

### 1. Registry Pattern
Tools self-register using a decorator:
```python
@ui_tool_registry.register
class MyTool(BaseUITool):
    ...
```

### 2. Strategy Pattern
Each UI component has its own strategy (tool) for loading context.

### 3. Template Method Pattern
`BaseUITool` defines the structure; subclasses implement specifics.

### 4. Dependency Injection
Database session and context injected into tools.

## 🔒 Error Handling

1. **No tool registered**: Returns error UIToolResult, falls back to legacy
2. **Database error**: Tool catches, logs, returns error UIToolResult
3. **Missing company_id**: Early validation, returns error
4. **Tool processing error**: Caught at dispatcher level

## 📈 Scalability

### Adding new tools:
1. Create file: `my_component.py`
2. Implement `BaseUITool`
3. Add `@ui_tool_registry.register` decorator
4. Import in `__init__.py`
5. Done - auto-registered

### Performance considerations:
- Tools run on every relevant request
- Database queries should be optimized
- Consider caching for expensive operations
- Tools run in parallel with ChatKit processing

## 🧪 Testing

Run test suite:
```bash
.venv/bin/python3 app/agents/ui_tools/test_ui_tools.py
```

Tests verify:
- Tool registration
- Dispatcher routing
- Interface compliance
- Error handling

## 🔮 Future Enhancements

- [ ] Caching layer for frequently accessed data
- [ ] Metrics/telemetry for tool performance
- [ ] Tool dependencies (tool A needs tool B's data)
- [ ] Async parallel tool execution
- [ ] Tool versioning for backwards compatibility
- [ ] Frontend component auto-discovery

## 📚 References

- Implementation examples: `contact_card.py`, `tax_summary_card.py`
- Template for new tools: `_template.py`
- User documentation: `README.md`
- Test suite: `test_ui_tools.py`
