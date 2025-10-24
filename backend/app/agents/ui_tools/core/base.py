"""Base classes for UI Tools system."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UIToolContext(BaseModel):
    """Context passed to UI tools for processing."""

    ui_component: str
    """Name of the UI component that triggered the interaction"""

    user_message: str
    """The user's message"""

    company_id: str | None = None
    """Company ID from the request context"""

    user_id: str | None = None
    """User ID from the request context"""

    db: AsyncSession | None = None
    """Database session for data fetching"""

    additional_data: dict[str, Any] = {}
    """Any additional context data from the request"""

    class Config:
        arbitrary_types_allowed = True


class UIToolResult(BaseModel):
    """Result returned by a UI tool after processing."""

    success: bool
    """Whether the tool successfully processed the request"""

    context_text: str
    """Formatted context text to prepend to agent instructions"""

    structured_data: dict[str, Any] = {}
    """Structured data that can be accessed by the agent"""

    metadata: dict[str, Any] = {}
    """Additional metadata about the processing"""

    error: str | None = None
    """Error message if processing failed"""


class BaseUITool(ABC):
    """
    Base class for all UI Tools.

    Each UI component should have a corresponding tool that:
    1. Fetches relevant data from the database
    2. Formats it into context for the agent
    3. Returns structured information
    """

    def __init__(self):
        """Initialize the UI tool."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def component_name(self) -> str:
        """
        The UI component name this tool handles.

        Must match the ui_component parameter sent from the frontend.
        Example: "contact_card", "tax_summary_card", "revenue_chart"
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what this tool does.

        Used for logging and documentation.
        """
        pass

    @property
    def domain(self) -> str:
        """
        The domain/category this tool belongs to.

        Examples: "contacts", "financials", "documents", "payroll"
        """
        return "general"

    @abstractmethod
    async def process(self, context: UIToolContext) -> UIToolResult:
        """
        Process the UI interaction and return enriched context.

        This is where you:
        1. Fetch data from the database
        2. Process/filter/aggregate as needed
        3. Format into human-readable context text
        4. Return structured data for agent use

        Args:
            context: Context information about the UI interaction

        Returns:
            UIToolResult with formatted context and structured data
        """
        pass

    def _format_context_section(self, title: str, content: str) -> str:
        """Helper to format a context section consistently."""
        return f"\n## {title}\n{content}\n"

    def _format_list(self, items: list[str]) -> str:
        """Helper to format a bulleted list."""
        return "\n".join(f"- {item}" for item in items)

    def _safe_get_uuid(self, value: str | None) -> UUID | None:
        """Safely convert a string to UUID, returning None if invalid."""
        if not value:
            return None
        try:
            return UUID(value)
        except (ValueError, AttributeError):
            self.logger.warning(f"Invalid UUID: {value}")
            return None
