"""Agent context for Fizko platform."""

from __future__ import annotations

from typing import Any

from chatkit.agents import AgentContext


class FizkoContext(AgentContext[dict[str, Any]]):
    """
    Context passed to all agents in the Fizko platform.

    Extends ChatKit's AgentContext with Fizko-specific fields.

    Attributes:
        thread: The current ChatKit thread metadata (inherited)
        store: The conversation store (inherited)
        request_context: Request-specific data - user_id, user, etc. (inherited)
        current_agent_type: The currently active agent
        thread_item_converter: Converter for attachments
    """

    current_agent_type: str = "sii_general"
    thread_item_converter: Any | None = None
