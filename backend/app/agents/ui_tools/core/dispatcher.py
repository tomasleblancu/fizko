"""Dispatcher for UI Tools - Routes UI interactions to appropriate tools."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .base import UIToolContext, UIToolResult
from .registry import ui_tool_registry

logger = logging.getLogger(__name__)


class UIToolDispatcher:
    """
    Dispatcher for UI Tools.

    Routes UI component interactions to their corresponding tools
    and handles the processing flow.
    """

    @staticmethod
    async def dispatch(
        ui_component: str | None,
        user_message: str,
        company_id: str | None = None,
        user_id: str | None = None,
        db: AsyncSession | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> UIToolResult | None:
        """
        Dispatch a UI component interaction to the appropriate tool.

        Args:
            ui_component: Name of the UI component (e.g., "contact_card")
            user_message: The user's message
            company_id: Company ID from request context
            user_id: User ID from request context
            db: Database session for data fetching
            additional_data: Any additional context data

        Returns:
            UIToolResult if a tool was found and executed, None otherwise
        """
        import time
        dispatch_start = time.time()

        # No component specified or "null" string
        if not ui_component or ui_component == "null":
            logger.debug("No ui_component specified, skipping dispatch")
            return None

        # Check if we have a tool for this component
        registry_lookup_start = time.time()
        tool = ui_tool_registry.get_tool(ui_component)
        logger.debug(f"  🔍 Registry lookup: {(time.time() - registry_lookup_start):.3f}s")

        if not tool:
            logger.warning(
                f"⚠️ No UI tool registered for component '{ui_component}'. "
                f"Available tools: {list(ui_tool_registry._tools.keys())}"
            )
            return UIToolResult(
                success=False,
                context_text="",
                error=f"No tool registered for UI component: {ui_component}",
                metadata={
                    "ui_component": ui_component,
                    "available_tools": list(ui_tool_registry._tools.keys()),
                },
            )

        # Create context for the tool
        context_create_start = time.time()
        context = UIToolContext(
            ui_component=ui_component,
            user_message=user_message,
            company_id=company_id,
            user_id=user_id,
            db=db,
            additional_data=additional_data or {},
        )
        logger.debug(f"  📦 Context creation: {(time.time() - context_create_start):.3f}s")

        # Execute the tool
        try:
            tool_exec_start = time.time()
            result = await tool.process(context)
            tool_exec_time = time.time() - tool_exec_start
            logger.debug(f"  🔧 Tool execution ({tool.__class__.__name__}): {tool_exec_time:.3f}s")

            if not result.success:
                logger.warning(
                    f"⚠️ UI tool failed: {ui_component} - {result.error}"
                )
            else:
                # Inject agent instructions if tool succeeded and has instructions
                if tool.agent_instructions:
                    instructions_text = tool.agent_instructions.strip()
                    if instructions_text:
                        # Prepend instructions to context_text with clear separator
                        result.context_text = (
                            f"{instructions_text}\n\n"
                            f"---\n\n"
                            f"{result.context_text}"
                        )
                        logger.debug(
                            f"  📝 Injected agent instructions ({len(instructions_text)} chars)"
                        )

            total_time = time.time() - dispatch_start
            logger.debug(f"  ✅ Total dispatch: {total_time:.3f}s")

            return result

        except Exception as e:
            logger.error(
                f"❌ Error processing UI tool '{ui_component}': {e}",
                exc_info=True,
            )
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error processing UI component: {str(e)}",
                metadata={
                    "ui_component": ui_component,
                    "exception": str(e),
                },
            )

    @staticmethod
    def list_registered_tools() -> list[tuple[str, str, str]]:
        """
        List all registered UI tools.

        Returns:
            List of (component_name, domain, description) tuples
        """
        return ui_tool_registry.list_tools()
