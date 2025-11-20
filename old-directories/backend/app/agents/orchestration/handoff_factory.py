"""Handoff factory module for creating validated agent handoffs."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from agents import Agent, handoff, RunContextWrapper
from pydantic import BaseModel

from ..core.subscription_responses import create_agent_block_response

logger = logging.getLogger(__name__)


class HandoffMetadata(BaseModel):
    """Metadata captured when a handoff occurs."""
    reason: str
    confidence: float | None = None


@dataclass
class HandoffConfig:
    """Configuration for an agent handoff."""
    agent_name: str  # e.g., "payroll"
    agent_key: str  # e.g., "payroll_agent"
    display_name: str  # e.g., "Payroll"
    icon: str  # e.g., "💼"
    description: str  # Tool description for LLM


class HandoffFactory:
    """
    Factory for creating validated agent handoffs.

    This class encapsulates the logic for creating handoffs that:
    1. Validate subscription access before transferring
    2. Return structured error responses when blocked
    3. Log handoff events with proper formatting
    4. Track active agent state for persistence
    """

    def __init__(self, agents: dict[str, Agent], session_manager: Any = None):
        """
        Initialize handoff factory.

        Args:
            agents: Dictionary of created agents (only available ones)
            session_manager: Optional SessionManager for tracking active agent
        """
        self.agents = agents
        self.session_manager = session_manager

    def create_validated_handoff(self, config: HandoffConfig) -> Any | None:
        """
        Create a handoff with subscription validation.

        Args:
            config: Handoff configuration

        Returns:
            Handoff object if agent is available, None otherwise
        """
        # Check if agent is available (was created)
        if config.agent_key not in self.agents:
            logger.debug(f"Agent {config.agent_name} not available, skipping handoff creation")
            return None

        # Create callback that validates before transfer
        async def on_handoff(
            ctx: RunContextWrapper, input_data: HandoffMetadata | None = None
        ):
            reason = input_data.reason if input_data else "No reason"

            # Double-check agent is available (defensive)
            if config.agent_key not in self.agents:
                logger.info(
                    f"🔒 Handoff blocked: {config.agent_name} | Reason: {reason}"
                )
                # Return block response for supervisor to process
                block_response = create_agent_block_response(config.agent_name)
                return block_response

            # Agent available - proceed with handoff
            agent = self.agents[config.agent_key]
            thread_id = ctx.context.request_context.get("thread_id", "unknown")

            logger.info(
                f"{config.icon} [HANDOFF] Supervisor → {config.display_name} | "
                f"Reason: {reason} | "
                f"Thread: {thread_id[:12] if thread_id != 'unknown' else 'unknown'}... | "
                f"Tools: {len(agent.tools)}"
            )

            # Track active agent for persistence (if session manager available)
            if self.session_manager:
                try:
                    if thread_id and thread_id != "unknown":
                        await self.session_manager.set_active_agent(
                            thread_id, config.agent_key
                        )
                        logger.info(
                            f"📍 [HANDOFF] Tracking {config.agent_key} as active for thread"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ [HANDOFF] Failed to track active agent: {e}")

        # Create handoff
        return handoff(
            agent=self.agents[config.agent_key],
            on_handoff=on_handoff,
            input_type=HandoffMetadata,
            tool_description_override=config.description,
        )

    def create_return_handoff(
        self,
        supervisor: Agent,
        description: str | None = None,
        enabled: bool = False
    ) -> Any:
        """
        Create a return-to-supervisor handoff for specialized agents.

        Args:
            supervisor: The supervisor agent to return to
            description: Optional custom description
            enabled: Whether handoff is enabled (default False)

        Returns:
            Handoff object
        """
        async def on_return_to_supervisor(
            ctx: RunContextWrapper, input_data: HandoffMetadata | None = None
        ):
            reason = input_data.reason if input_data else "Topic change"
            thread_id = ctx.context.request_context.get("thread_id", "unknown")

            logger.info(
                f"🔄 [HANDOFF] Agent → Supervisor | "
                f"Reason: {reason} | "
                f"Thread: {thread_id[:12] if thread_id != 'unknown' else 'unknown'}..."
            )

            # Clear active agent (return to supervisor)
            if self.session_manager:
                try:
                    if thread_id and thread_id != "unknown":
                        await self.session_manager.clear_active_agent(thread_id)
                        logger.info(f"🗑️ [HANDOFF] Cleared active agent, back to supervisor")
                except Exception as e:
                    logger.warning(f"⚠️ [HANDOFF] Failed to clear active agent: {e}")

        default_description = (
            "Return to main menu ONLY if user explicitly requests a completely different topic "
            "(e.g., switching from documents to tax concepts, or vice versa). "
            "Do NOT use for simple acknowledgments like 'thanks', 'ok', 'got it'. "
            "Stay in current conversation for follow-up questions."
        )

        return handoff(
            agent=supervisor,
            on_handoff=on_return_to_supervisor,
            input_type=HandoffMetadata,
            tool_name_override="return_to_main_menu",
            tool_description_override=description or default_description,
            is_enabled=enabled,
        )

    @staticmethod
    def get_standard_configs() -> list[HandoffConfig]:
        """
        Get standard handoff configurations for all agents.

        Returns:
            List of HandoffConfig objects
        """
        return [
            HandoffConfig(
                agent_name="general_knowledge",
                agent_key="general_knowledge_agent",
                display_name="General Knowledge",
                icon="🧠",
                description=(
                    "Transfer to General Knowledge expert for conceptual questions, "
                    "tax theory, definitions, deadlines, and educational queries. "
                    "Provide a brief reason for the transfer."
                ),
            ),
            HandoffConfig(
                agent_name="tax_documents",
                agent_key="tax_documents_agent",
                display_name="Tax Documents",
                icon="📄",
                description=(
                    "Transfer to Tax Documents expert for real document data, "
                    "invoices, receipts, summaries, and document searches. "
                    "Provide a brief reason for the transfer."
                ),
            ),
            HandoffConfig(
                agent_name="f29",
                agent_key="monthly_taxes_agent",
                display_name="Monthly Taxes Expert",
                icon="📋",
                description=(
                    "Transfer to Monthly Taxes expert for Formulario 29 questions, "
                    "F29 visualizations, explanations, and tax declarations. "
                    "Provide a brief reason for the transfer."
                ),
            ),
            HandoffConfig(
                agent_name="payroll",
                agent_key="payroll_agent",
                display_name="Payroll",
                icon="💼",
                description=(
                    "Transfer to Payroll expert for labor law questions, "
                    "employee management, payroll processing, and work contracts. "
                    "Provide a brief reason for the transfer."
                ),
            ),
            HandoffConfig(
                agent_name="settings",
                agent_key="settings_agent",
                display_name="Settings",
                icon="⚙️",
                description=(
                    "Transfer to Settings expert for managing user preferences, "
                    "notification settings, and account configuration. "
                    "Provide a brief reason for the transfer."
                ),
            ),
            HandoffConfig(
                agent_name="expense",
                agent_key="expense_agent",
                display_name="Expense Management",
                icon="💰",
                description=(
                    "Transfer to Expense Management expert for registering and managing "
                    "manual expenses, expense receipts, OCR extraction, and expense tracking. "
                    "Provide a brief reason for the transfer."
                ),
            ),
            HandoffConfig(
                agent_name="feedback",
                agent_key="feedback_agent",
                display_name="Feedback & Support",
                icon="💬",
                description=(
                    "Transfer to Feedback expert for collecting user feedback, bug reports, "
                    "feature requests, and platform issues. Use when user reports problems "
                    "or suggests improvements to the platform itself. "
                    "Provide a brief reason for the transfer."
                ),
            ),
        ]
