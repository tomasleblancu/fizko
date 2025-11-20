"""
UI Tools Module - Pre-loads context for UI components (Supabase Version).

This module provides a system to automatically fetch and prepare
relevant context when a user interacts with specific UI components,
so the agent receives enriched, ready-to-use information.

Architecture:
- Each UI component has a corresponding tool in tools/
- Tools implement the BaseUITool interface (in core/)
- The UIToolDispatcher (in core/) automatically routes to the right tool
- Context is pre-loaded before the agent processes the message
- **Uses Supabase client instead of SQLAlchemy for database access**

Example:
    When user clicks on a contact card in the frontend:
    1. Frontend sends: ui_component="contact_card"
    2. Backend dispatches to ContactCardTool
    3. Tool fetches contact info from Supabase
    4. Agent receives enriched context with contact data

TEMPORARY: Only ContactCardTool is enabled.
Other tools need migration to Supabase.
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
# TEMPORARY: Only ContactCardTool is migrated to Supabase
from .tools import (
    ContactCardTool,
    # TODO: Migrate these to Supabase
    # TaxSummaryIVATool,
    # TaxSummaryRevenueTool,
    # TaxSummaryExpensesTool,
)

__all__ = [
    # Core infrastructure
    "BaseUITool",
    "UIToolContext",
    "UIToolResult",
    "UIToolDispatcher",
    "UIToolRegistry",
    "ui_tool_registry",
    # Specific tools (only migrated ones)
    "ContactCardTool",
    # TODO: Add back after migration
    # "TaxSummaryIVATool",
    # "TaxSummaryRevenueTool",
    # "TaxSummaryExpensesTool",
]
