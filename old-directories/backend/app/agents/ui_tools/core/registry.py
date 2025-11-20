"""Registry for UI Tools - Automatic discovery and registration."""

from __future__ import annotations

import logging
from typing import Type

from .base import BaseUITool

logger = logging.getLogger(__name__)


class UIToolRegistry:
    """
    Registry for UI Tools.

    Automatically manages UI tool registration and lookup.
    Each UI tool registers itself when imported.
    """

    def __init__(self):
        """Initialize the registry."""
        self._tools: dict[str, BaseUITool] = {}
        self._tool_classes: dict[str, Type[BaseUITool]] = {}

    def register(self, tool_class: Type[BaseUITool]) -> Type[BaseUITool]:
        """
        Register a UI tool class.

        This is meant to be used as a decorator:

        @ui_tool_registry.register
        class MyUITool(BaseUITool):
            ...

        Args:
            tool_class: The UI tool class to register

        Returns:
            The same class (for decorator usage)
        """
        # Instantiate the tool
        tool_instance = tool_class()
        component_name = tool_instance.component_name

        if component_name in self._tools:
            logger.warning(
                f"UI tool for '{component_name}' already registered. "
                f"Overwriting with {tool_class.__name__}"
            )

        self._tools[component_name] = tool_instance
        self._tool_classes[component_name] = tool_class

        logger.info(
            f"✅ Registered UI tool: {tool_class.__name__} "
            f"for component '{component_name}' (domain: {tool_instance.domain})"
        )

        return tool_class

    def get_tool(self, component_name: str) -> BaseUITool | None:
        """
        Get a UI tool instance by component name.

        Args:
            component_name: The UI component name (e.g., "contact_card")

        Returns:
            The UI tool instance, or None if not found
        """
        return self._tools.get(component_name)

    def has_tool(self, component_name: str) -> bool:
        """
        Check if a tool is registered for a component.

        Args:
            component_name: The UI component name

        Returns:
            True if a tool is registered, False otherwise
        """
        return component_name in self._tools

    def list_tools(self) -> list[tuple[str, str, str]]:
        """
        List all registered tools.

        Returns:
            List of (component_name, domain, description) tuples
        """
        return [
            (name, tool.domain, tool.description)
            for name, tool in self._tools.items()
        ]

    def get_tools_by_domain(self, domain: str) -> list[BaseUITool]:
        """
        Get all tools in a specific domain.

        Args:
            domain: The domain to filter by

        Returns:
            List of UI tools in that domain
        """
        return [
            tool for tool in self._tools.values()
            if tool.domain == domain
        ]


# Global registry instance
ui_tool_registry = UIToolRegistry()
