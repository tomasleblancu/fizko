"""Agent context for Fizko platform - Simplified for Backend V2."""

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
        request_context: Request-specific data - user_id, company_id, etc. (inherited)
        current_agent_type: The currently active agent
        company_info: Preloaded company information (RUT, name, tax info, etc.)
    """

    current_agent_type: str = "sii_general"
    company_info: dict[str, Any] | None = None
