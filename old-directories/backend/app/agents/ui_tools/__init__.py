"""
UI Tools Module - Pre-loads context for UI components.

This module provides a system to automatically fetch and prepare
relevant context when a user interacts with specific UI components,
so the agent receives enriched, ready-to-use information.

Architecture:
- Each UI component has a corresponding tool in tools/
- Tools implement the BaseUITool interface (in core/)
- The UIToolDispatcher (in core/) automatically routes to the right tool
- Context is pre-loaded before the agent processes the message

Example:
    When user clicks on a contact card in the frontend:
    1. Frontend sends: ui_component="contact_card"
    2. Backend dispatches to ContactCardTool
    3. Tool fetches contact info from DB
    4. Agent receives enriched context with contact data
"""

# Export core infrastructure
from .core import (
    BaseUITool,
    UIToolContext,
    UIToolResult,
    UIToolDispatcher,
    UIToolRegistry,
    ui_tool_registry,
)

# Import tools to trigger auto-registration
# The @ui_tool_registry.register decorator runs when modules are imported
from .tools import (
    ContactCardTool,
    TaxSummaryIVATool,
    TaxSummaryRevenueTool,
    TaxSummaryExpensesTool,
)

__all__ = [
    # Core infrastructure
    "BaseUITool",
    "UIToolContext",
    "UIToolResult",
    "UIToolDispatcher",
    "UIToolRegistry",
    "ui_tool_registry",
    # Specific tools
    "ContactCardTool",
    "TaxSummaryIVATool",
    "TaxSummaryRevenueTool",
    "TaxSummaryExpensesTool",
]
