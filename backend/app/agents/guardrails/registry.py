"""Guardrail Registry - Centralized registration and management of guardrails."""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class GuardrailRegistry:
    """
    Central registry for all guardrails.

    This allows:
    - Discovering available guardrails
    - Enabling/disabling guardrails per company/user
    - Audit logging of guardrail usage
    - A/B testing different guardrail configurations

    Usage:
        # Register a guardrail (usually done at module import time)
        @input_guardrail
        async def my_guardrail(...):
            ...

        guardrail_registry.register(
            name="abuse_detection",
            guardrail_func=my_guardrail,
            category="safety",
            enabled_by_default=True,
        )

        # Get guardrails for an agent
        input_guardrails = guardrail_registry.get_input_guardrails_for_agent(
            agent_name="supervisor_agent",
            company_id=company_id,
        )
    """

    def __init__(self):
        self._input_guardrails: dict[str, dict[str, Any]] = {}
        self._output_guardrails: dict[str, dict[str, Any]] = {}

    def register_input_guardrail(
        self,
        name: str,
        guardrail_func: Callable,
        category: str = "general",
        enabled_by_default: bool = True,
        description: str | None = None,
    ):
        """
        Register an input guardrail.

        Args:
            name: Unique name for the guardrail
            guardrail_func: The guardrail function (decorated with @input_guardrail)
            category: Category (e.g., "safety", "compliance", "subscription")
            enabled_by_default: Whether to enable by default
            description: Human-readable description
        """
        if name in self._input_guardrails:
            logger.warning(f"⚠️  Input guardrail '{name}' already registered, overwriting")

        self._input_guardrails[name] = {
            "name": name,
            "func": guardrail_func,
            "category": category,
            "enabled_by_default": enabled_by_default,
            "description": description or getattr(guardrail_func, "_guardrail_description", "No description"),
            "is_input": True,
        }

        logger.info(f"📝 Registered input guardrail: {name} (category: {category})")

    def register_output_guardrail(
        self,
        name: str,
        guardrail_func: Callable,
        category: str = "general",
        enabled_by_default: bool = True,
        description: str | None = None,
    ):
        """
        Register an output guardrail.

        Args:
            name: Unique name for the guardrail
            guardrail_func: The guardrail function (decorated with @output_guardrail)
            category: Category (e.g., "safety", "compliance", "pii")
            enabled_by_default: Whether to enable by default
            description: Human-readable description
        """
        if name in self._output_guardrails:
            logger.warning(f"⚠️  Output guardrail '{name}' already registered, overwriting")

        self._output_guardrails[name] = {
            "name": name,
            "func": guardrail_func,
            "category": category,
            "enabled_by_default": enabled_by_default,
            "description": description or getattr(guardrail_func, "_guardrail_description", "No description"),
            "is_input": False,
        }

        logger.info(f"📝 Registered output guardrail: {name} (category: {category})")

    def get_input_guardrails_for_agent(
        self,
        agent_name: str,
        company_id: str | None = None,
        enabled_only: bool = True,
    ) -> list[Callable]:
        """
        Get input guardrails for a specific agent.

        Args:
            agent_name: Name of the agent
            company_id: Company ID (for per-company configuration)
            enabled_only: Only return enabled guardrails

        Returns:
            List of guardrail functions
        """
        # TODO: Implement per-agent, per-company configuration
        # For now, return all enabled guardrails
        guardrails = []
        for info in self._input_guardrails.values():
            if enabled_only and not info["enabled_by_default"]:
                continue
            guardrails.append(info["func"])

        return guardrails

    def get_output_guardrails_for_agent(
        self,
        agent_name: str,
        company_id: str | None = None,
        enabled_only: bool = True,
    ) -> list[Callable]:
        """
        Get output guardrails for a specific agent.

        Args:
            agent_name: Name of the agent
            company_id: Company ID (for per-company configuration)
            enabled_only: Only return enabled guardrails

        Returns:
            List of guardrail functions
        """
        # TODO: Implement per-agent, per-company configuration
        # For now, return all enabled guardrails
        guardrails = []
        for info in self._output_guardrails.values():
            if enabled_only and not info["enabled_by_default"]:
                continue
            guardrails.append(info["func"])

        return guardrails

    def list_all(self) -> dict[str, Any]:
        """
        List all registered guardrails.

        Returns:
            Dict with "input" and "output" keys containing guardrail info
        """
        return {
            "input": [
                {
                    "name": info["name"],
                    "category": info["category"],
                    "enabled_by_default": info["enabled_by_default"],
                    "description": info["description"],
                }
                for info in self._input_guardrails.values()
            ],
            "output": [
                {
                    "name": info["name"],
                    "category": info["category"],
                    "enabled_by_default": info["enabled_by_default"],
                    "description": info["description"],
                }
                for info in self._output_guardrails.values()
            ],
        }

    def get_guardrail(self, name: str, is_input: bool = True) -> Callable | None:
        """
        Get a specific guardrail by name.

        Args:
            name: Guardrail name
            is_input: Whether to look in input or output guardrails

        Returns:
            Guardrail function or None if not found
        """
        registry = self._input_guardrails if is_input else self._output_guardrails
        info = registry.get(name)
        return info["func"] if info else None


# Global registry instance
guardrail_registry = GuardrailRegistry()
