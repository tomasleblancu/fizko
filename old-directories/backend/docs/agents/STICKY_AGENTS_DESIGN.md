# Sticky Agents Design - Agent Persistence System

## Overview

This document describes the **Sticky Agents** feature - a system that makes agents "stick" after the supervisor hands off to them, so subsequent messages go directly to the active agent without routing through the supervisor.

## Current Architecture (Before)

```
User Message 1 → Supervisor → [Handoff] → Tax Documents Agent
User Message 2 → Supervisor → [Handoff] → Tax Documents Agent  ❌ Inefficient
User Message 3 → Supervisor → [Handoff] → Tax Documents Agent  ❌ Inefficient
```

**Problems:**
1. Every message goes through supervisor (unnecessary routing)
2. SessionManager stores active agent in memory only (lost between instances)
3. ~200-300ms overhead per message for supervisor routing
4. No explicit "return to supervisor" mechanism for users

## Target Architecture (After)

```
User Message 1 → Supervisor → [Handoff] → Tax Documents Agent → Save to thread context
User Message 2 → Read from thread context → Tax Documents Agent directly ✅
User Message 3 → Read from thread context → Tax Documents Agent directly ✅
User types "/supervisor" → Clear thread context → Return to Supervisor ✅
```

**Benefits:**
1. Direct routing to active agent (50-100ms saved per message)
2. Persistent across server restarts (stored in ChatKit thread context)
3. User can explicitly return to supervisor with command
4. Better conversation continuity and context retention

---

## Implementation Plan

### Phase 1: Thread Context Integration

#### 1.1 Enhance SessionManager with ChatKit Integration

**File:** `backend/app/agents/orchestration/session_manager.py`

**Changes:**
```python
class SessionManager:
    """Manages agent session state with ChatKit thread context persistence."""

    THREAD_CONTEXT_KEY = "active_agent"  # Key for storing in thread context

    def __init__(self):
        self._active_agents: dict[str, str] = {}  # In-memory cache
        self._chatkit_thread = None  # Will hold ChatKit thread instance

    def set_thread_instance(self, thread):
        """Set ChatKit thread instance for persistence."""
        self._chatkit_thread = thread

    async def get_active_agent(self, thread_id: str) -> str | None:
        """
        Get active agent with fallback chain:
        1. Check in-memory cache (fast path)
        2. Read from ChatKit thread context (persistent)
        3. Return None if not found
        """
        # Fast path: in-memory cache
        if thread_id in self._active_agents:
            return self._active_agents[thread_id]

        # Slow path: read from thread context (persistent)
        if self._chatkit_thread:
            try:
                context = await self._chatkit_thread.get_context()
                active_agent = context.get(self.THREAD_CONTEXT_KEY)

                if active_agent:
                    # Cache it for future requests
                    self._active_agents[thread_id] = active_agent
                    logger.info(f"📌 Restored active agent from thread context: {active_agent}")
                    return active_agent
            except Exception as e:
                logger.warning(f"Failed to read from thread context: {e}")

        return None

    async def set_active_agent(self, thread_id: str, agent_key: str) -> bool:
        """
        Set active agent in both memory and thread context.
        """
        # Set in memory
        self._active_agents[thread_id] = agent_key

        # Persist to thread context
        if self._chatkit_thread:
            try:
                await self._chatkit_thread.update_context({
                    self.THREAD_CONTEXT_KEY: agent_key
                })
                logger.info(f"✅ Persisted active agent to thread context: {agent_key}")
            except Exception as e:
                logger.warning(f"Failed to persist to thread context: {e}")
                return False

        return True

    async def clear_active_agent(self, thread_id: str) -> bool:
        """
        Clear active agent from memory and thread context.
        """
        # Clear from memory
        if thread_id in self._active_agents:
            del self._active_agents[thread_id]

        # Clear from thread context
        if self._chatkit_thread:
            try:
                await self._chatkit_thread.update_context({
                    self.THREAD_CONTEXT_KEY: None
                })
                logger.info(f"🧹 Cleared active agent from thread context")
            except Exception as e:
                logger.warning(f"Failed to clear thread context: {e}")
                return False

        return True
```

**Rationale:**
- Two-tier storage: in-memory cache (fast) + thread context (persistent)
- Survives server restarts and multi-instance deployments
- Graceful degradation if thread context unavailable

---

#### 1.2 Modify HandoffsManager to Support Direct Agent Access

**File:** `backend/app/agents/orchestration/handoffs_manager.py`

**Add new method:**
```python
async def get_active_or_supervisor_agent(
    self,
    thread_id: str,
    db: AsyncSession,
    user_id: str | None = None,
    company_id: UUID | None = None,
    vector_store_ids: list[str] | None = None,
    channel: str = "web",
    chatkit_thread = None,  # NEW: Pass ChatKit thread instance
) -> Agent:
    """
    Get the active agent if one exists, otherwise return supervisor.

    This enables "sticky agents" - once a user is handed off to a specialist,
    subsequent messages go directly to that agent.

    Args:
        thread_id: ChatKit thread ID
        db: Database session
        user_id: Optional user ID
        company_id: Optional company ID
        vector_store_ids: Optional vector store IDs
        channel: Communication channel
        chatkit_thread: ChatKit thread instance for context persistence

    Returns:
        Active agent if exists, otherwise supervisor agent
    """
    # Get orchestrator (creates agents)
    orchestrator = await self.get_orchestrator(
        thread_id=thread_id,
        db=db,
        user_id=user_id,
        company_id=company_id,
        vector_store_ids=vector_store_ids,
        channel=channel,
    )

    # Set thread instance for persistence
    if chatkit_thread:
        orchestrator.session_manager.set_thread_instance(chatkit_thread)

    # Check for active agent
    active_agent = await orchestrator.get_active_agent()

    if active_agent:
        agent_name = getattr(active_agent, 'name', 'unknown')
        logger.info(f"🎯 Using active agent: {agent_name} (thread: {thread_id[:8]})")
        return active_agent

    # No active agent - return supervisor
    logger.info(f"👔 Using supervisor (no active agent, thread: {thread_id[:8]})")
    return orchestrator.get_supervisor_agent()
```

**Rationale:**
- Single entry point for "active or supervisor" logic
- Integrates thread context for persistence
- Logs routing decisions for debugging

---

### Phase 2: Router Integration

#### 2.1 Modify ChatKit Endpoint to Use Active Agent

**File:** `backend/app/routers/chat/chatkit.py`

**Current code (line 280-290):**
```python
# Process request through ChatKit server
try:
    result = await server.process(payload, context)
```

**Change to:**
```python
# Get the appropriate agent (active or supervisor)
from ...agents.orchestration.handoffs_manager import handoffs_manager

async with AsyncSessionLocal() as db:
    # Extract thread_id from payload
    thread_id = None
    try:
        payload_dict = json.loads(payload)
        thread_id = payload_dict.get("thread_id")
    except:
        pass

    if not thread_id:
        logger.warning("⚠️ No thread_id in payload, using supervisor")
        # Fallback to supervisor
        agent = await handoffs_manager.get_supervisor_agent(
            thread_id="default",
            db=db,
            user_id=user_id,
            company_id=company_id,
            channel="chatkit",
        )
    else:
        # Get active agent or supervisor
        agent = await handoffs_manager.get_active_or_supervisor_agent(
            thread_id=thread_id,
            db=db,
            user_id=user_id,
            company_id=company_id,
            channel="chatkit",
            chatkit_thread=server.get_thread(thread_id),  # Pass thread for persistence
        )

# Update context with selected agent
context["agent"] = agent
context["agent_name"] = getattr(agent, 'name', 'unknown')

# Process request through ChatKit server
try:
    result = await server.process(payload, context)
```

**Rationale:**
- Routes to active agent when available
- Falls back to supervisor for new conversations
- Passes thread instance for context persistence

---

### Phase 3: User Commands for Control

#### 3.1 Add Command Detection in Message Processing

**File:** `backend/app/agents/core/message_processor.py` (new file)

```python
"""Message processing utilities for agent system."""

import logging
import re

logger = logging.getLogger(__name__)

# Command patterns
COMMAND_PATTERNS = {
    "supervisor": re.compile(r"^/supervisor\b", re.IGNORECASE),
    "reset": re.compile(r"^/reset\b", re.IGNORECASE),
    "agents": re.compile(r"^/agents\b", re.IGNORECASE),
    "status": re.compile(r"^/status\b", re.IGNORECASE),
}


def detect_command(message: str) -> tuple[str | None, str]:
    """
    Detect user commands in messages.

    Args:
        message: User message text

    Returns:
        Tuple of (command_name, cleaned_message)
        command_name is None if no command detected
    """
    message = message.strip()

    for command_name, pattern in COMMAND_PATTERNS.items():
        if pattern.match(message):
            # Remove command from message
            cleaned = pattern.sub("", message).strip()
            logger.info(f"🎮 Detected command: /{command_name}")
            return command_name, cleaned

    return None, message


async def handle_command(
    command: str,
    orchestrator,
    thread_id: str,
) -> str | None:
    """
    Handle user commands.

    Args:
        command: Command name (without /)
        orchestrator: MultiAgentOrchestrator instance
        thread_id: ChatKit thread ID

    Returns:
        Response message if command handled, None otherwise
    """
    if command == "supervisor":
        # Clear active agent and return to supervisor
        await orchestrator.clear_active_agent()
        return (
            "✅ Regresaste al asistente principal.\n\n"
            "Ahora puedo ayudarte con cualquier tema:\n"
            "• Documentos tributarios\n"
            "• Impuestos mensuales (F29)\n"
            "• Remuneraciones y personal\n"
            "• Configuración\n"
            "• O cualquier otra consulta\n\n"
            "¿En qué puedo ayudarte?"
        )

    elif command == "reset":
        # Same as supervisor for now
        await orchestrator.clear_active_agent()
        return "🔄 Conversación reiniciada. ¿En qué puedo ayudarte?"

    elif command == "agents":
        # List available agents
        agents = orchestrator.list_agents()
        agent_list = "\n".join([f"• {agent}" for agent in agents])
        return f"🤖 Agentes disponibles:\n{agent_list}"

    elif command == "status":
        # Show current agent status
        active_agent = await orchestrator.get_active_agent()
        if active_agent:
            agent_name = getattr(active_agent, 'name', 'unknown')
            return f"📊 Agente activo: **{agent_name}**\n\nEscribe `/supervisor` para volver al asistente principal."
        else:
            return "📊 Estás hablando con el **asistente principal** (supervisor)."

    return None
```

**Rationale:**
- Simple command pattern matching
- Extensible for future commands
- User-friendly Spanish responses

---

#### 3.2 Integrate Command Detection in Router

**File:** `backend/app/routers/chat/chatkit.py`

**Add after extracting user_message (around line 220):**
```python
from ...agents.core.message_processor import detect_command, handle_command

# Detect commands
command, cleaned_message = detect_command(user_message)

if command:
    # Handle command immediately
    async with AsyncSessionLocal() as db:
        orchestrator = await handoffs_manager.get_orchestrator(
            thread_id=thread_id or "default",
            db=db,
            user_id=user_id,
            company_id=company_id,
            channel="chatkit",
        )

        response = await handle_command(command, orchestrator, thread_id or "default")

        if response:
            # Return command response directly
            return JSONResponse({
                "role": "assistant",
                "content": [{"type": "output_text", "text": response}]
            })
```

**Rationale:**
- Commands processed before agent routing
- Fast path for system commands
- Doesn't consume agent API calls

---

### Phase 4: Automatic Active Agent Tracking

#### 4.1 Hook into Handoff Events

**File:** `backend/app/agents/orchestration/handoff_factory.py`

**Modify handoff on_transfer callback:**
```python
def create_validated_handoff(self, config: HandoffConfig) -> Handoff | None:
    """Create a handoff with subscription validation and persistence tracking."""
    # ... existing validation code ...

    # Wrap on_transfer to track active agent
    original_on_transfer = config.on_transfer

    async def on_transfer_with_tracking(ctx):
        # Call original callback
        if original_on_transfer:
            await original_on_transfer(ctx)

        # Save active agent to session
        target_agent_key = config.to_key
        if self.session_manager:
            thread_id = getattr(ctx, 'thread_id', None)
            if thread_id:
                await self.session_manager.set_active_agent(thread_id, target_agent_key)
                logger.info(f"📌 Tracked handoff to: {target_agent_key}")

    config.on_transfer = on_transfer_with_tracking

    return Handoff(
        # ... existing handoff creation ...
    )
```

**Rationale:**
- Automatic tracking on every handoff
- No manual calls needed in agent code
- Centralized in handoff factory

---

## Testing Plan

### Unit Tests

```python
# tests/test_sticky_agents.py

import pytest
from backend.app.agents.orchestration.session_manager import SessionManager

@pytest.mark.asyncio
async def test_session_manager_memory():
    """Test in-memory caching."""
    manager = SessionManager()

    await manager.set_active_agent("thread-123", "tax_agent")
    active = await manager.get_active_agent("thread-123")

    assert active == "tax_agent"

@pytest.mark.asyncio
async def test_session_manager_persistence(mock_chatkit_thread):
    """Test thread context persistence."""
    manager = SessionManager()
    manager.set_thread_instance(mock_chatkit_thread)

    await manager.set_active_agent("thread-123", "tax_agent")

    # Simulate server restart - clear memory
    manager._active_agents.clear()

    # Should restore from thread context
    active = await manager.get_active_agent("thread-123")
    assert active == "tax_agent"

@pytest.mark.asyncio
async def test_command_detection():
    """Test command detection."""
    from backend.app.agents.core.message_processor import detect_command

    cmd, msg = detect_command("/supervisor")
    assert cmd == "supervisor"
    assert msg == ""

    cmd, msg = detect_command("/supervisor show me taxes")
    assert cmd == "supervisor"
    assert msg == "show me taxes"

    cmd, msg = detect_command("regular message")
    assert cmd is None
    assert msg == "regular message"
```

### Integration Tests

```python
# tests/integration/test_sticky_agents_flow.py

@pytest.mark.asyncio
async def test_sticky_agent_flow(client, db):
    """Test complete sticky agent flow."""

    # 1. First message → Supervisor routes to Tax Agent
    response1 = await client.post("/chatkit", json={
        "thread_id": "test-thread-1",
        "text": "muestra mis facturas",
    })
    assert response1.status_code == 200
    # Verify Tax Agent responded

    # 2. Second message → Should go directly to Tax Agent
    response2 = await client.post("/chatkit", json={
        "thread_id": "test-thread-1",
        "text": "cuántas tengo?",
    })
    assert response2.status_code == 200
    # Verify Tax Agent responded (not supervisor)

    # 3. User returns to supervisor
    response3 = await client.post("/chatkit", json={
        "thread_id": "test-thread-1",
        "text": "/supervisor",
    })
    assert response3.status_code == 200
    # Verify confirmation message

    # 4. Next message → Should go to Supervisor
    response4 = await client.post("/chatkit", json={
        "thread_id": "test-thread-1",
        "text": "ayúdame con el F29",
    })
    assert response4.status_code == 200
    # Verify Supervisor routed to F29 Agent
```

---

## Performance Considerations

### Before (Current):
```
User Message → Supervisor (100-200ms) → Specialist Agent (200-300ms) = 300-500ms total
```

### After (Sticky Agents):
```
First Message → Supervisor (100-200ms) → Specialist Agent (200-300ms) = 300-500ms
Subsequent Messages → Specialist Agent (50-100ms) = 50-100ms total ✅
```

**Savings:** 200-400ms per message after first handoff (60-80% reduction)

### Memory Impact:
- In-memory cache: ~50 bytes per thread (negligible)
- Thread context: Already exists in ChatKit (no additional storage)

---

## Migration Path

### Phase 1: Development (Week 1)
- [ ] Implement SessionManager enhancements
- [ ] Add HandoffsManager.get_active_or_supervisor_agent()
- [ ] Write unit tests

### Phase 2: Integration (Week 2)
- [ ] Integrate with chatkit.py router
- [ ] Add command detection system
- [ ] Write integration tests

### Phase 3: Testing (Week 3)
- [ ] User acceptance testing
- [ ] Performance benchmarking
- [ ] Bug fixes

### Phase 4: Production (Week 4)
- [ ] Deploy to staging
- [ ] Monitor metrics
- [ ] Deploy to production
- [ ] Documentation updates

---

## Rollback Plan

If issues arise:

1. **Feature flag:** Add `ENABLE_STICKY_AGENTS` env var
2. **Fallback:** Keep old code path as backup
3. **Quick rollback:** Set flag to `false` to revert to supervisor-only routing

```python
# In chatkit.py
if os.getenv("ENABLE_STICKY_AGENTS", "true").lower() == "true":
    agent = await handoffs_manager.get_active_or_supervisor_agent(...)
else:
    agent = await handoffs_manager.get_supervisor_agent(...)
```

---

## Success Metrics

### Performance:
- **Target:** 50-80% reduction in response time for follow-up messages
- **Measure:** Average response time before/after for threads with 3+ messages

### User Experience:
- **Target:** <5% user reports of "getting stuck" with wrong agent
- **Measure:** Support tickets + command usage (`/supervisor` frequency)

### System Health:
- **Target:** No increase in error rate
- **Measure:** Error logs for agent routing failures

---

## Future Enhancements

### 1. Smart Agent Switching
Detect topic changes and suggest agent switching:
```
User: "ahora muéstrame el F29"
Tax Agent: "🔄 Parece que quieres consultar el F29. ¿Te conecto con el especialista de impuestos mensuales? [Sí] [No, continúa aquí]"
```

### 2. Agent History
Show conversation history per agent:
```
User: "/history"
Response:
📚 Historial de conversación:
• Tax Documents Agent (10 mensajes)
• F29 Agent (5 mensajes)
• Supervisor (2 mensajes)
```

### 3. Multi-Agent Collaboration
Allow agents to collaborate on complex queries:
```
Tax Agent: "Para responder esto necesito datos del F29. ¿Consulto con el agente de impuestos mensuales?"
```

---

## References

- **ChatKit Thread Context:** https://docs.chatkit.ai/thread-context
- **Agent Handoffs:** [MULTI_AGENT_ARCHITECTURE.md](./MULTI_AGENT_ARCHITECTURE.md#handoff-system)
- **SessionManager:** [session_manager.py](../../app/agents/orchestration/session_manager.py)
- **HandoffsManager:** [handoffs_manager.py](../../app/agents/orchestration/handoffs_manager.py)
