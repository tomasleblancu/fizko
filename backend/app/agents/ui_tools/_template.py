"""
UI Tool Template - Copy this file to create a new UI Tool.

Steps:
1. Copy this file and rename it (e.g., my_component.py)
2. Replace "MyComponent" with your component name
3. Implement the _fetch_data and _format_context methods
4. Import in __init__.py to auto-register
5. Test with test_ui_tools.py

Example: See contact_card.py and tax_summary_card.py for complete implementations
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import Company  # Import your models here
from .core.base import BaseUITool, UIToolContext, UIToolResult
from .core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register  # This decorator auto-registers your tool
class MyComponentTool(BaseUITool):
    """
    UI Tool for [Component Name] component.

    [Describe what data this tool pre-loads and when it's used]

    Example:
        When a user views [component description], this tool loads:
        - [Data point 1]
        - [Data point 2]
        - [Data point 3]
    """

    @property
    def component_name(self) -> str:
        """
        Must match the ui_component parameter from the frontend.

        Example: "my_component" matches frontend code:
            <ChateableWrapper uiComponent="my_component">
        """
        return "my_component"  # TODO: Change this

    @property
    def description(self) -> str:
        """Human-readable description for logging and docs."""
        return "TODO: Describe what this tool does"

    @property
    def domain(self) -> str:
        """
        Domain/category for this tool.

        Common domains:
        - "contacts"
        - "financials"
        - "tax_compliance"
        - "documents"
        - "payroll"
        - "general"
        """
        return "general"  # TODO: Change this

    async def process(self, context: UIToolContext) -> UIToolResult:
        """
        Process the UI interaction and return enriched context.

        This is the main entry point. Follow this pattern:
        1. Validate required context
        2. Fetch data from database
        3. Format into human-readable text
        4. Return UIToolResult
        """

        # Step 1: Validate context
        if not context.db:
            return UIToolResult(
                success=False,
                context_text="",
                error="Database session not available",
            )

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        # Step 2: Fetch data
        try:
            data = await self._fetch_data(
                db=context.db,
                company_id=context.company_id,
                user_message=context.user_message,
                additional_data=context.additional_data,
            )

            if not data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No data found",  # TODO: Better error message
                )

            # Step 3: Format context
            context_text = self._format_context(data)

            # Step 4: Return result
            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=data,
                metadata={
                    # Add useful metadata for logging/debugging
                    "data_count": len(data) if isinstance(data, list) else 1,
                    # TODO: Add more metadata as needed
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing {self.component_name}: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error processing component: {str(e)}",
            )

    async def _fetch_data(
        self,
        db: AsyncSession,
        company_id: str,
        user_message: str,
        additional_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Fetch relevant data from the database.

        This is where you implement your custom data-fetching logic.

        Args:
            db: Database session
            company_id: Company UUID string
            user_message: User's message (may contain filters/parameters)
            additional_data: Extra data from request context

        Returns:
            Dictionary with fetched data, or None if not found
        """
        # Convert company_id to UUID
        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return None

        # TODO: Implement your database queries here
        # Example:
        # stmt = select(MyModel).where(
        #     MyModel.company_id == company_uuid
        # )
        # result = await db.execute(stmt)
        # my_data = result.scalars().all()
        #
        # return {
        #     "items": [item.to_dict() for item in my_data],
        #     "count": len(my_data),
        #     # ... more data
        # }

        # Placeholder - remove this and add your logic
        return {
            "placeholder": "Implement _fetch_data method",
        }

    def _format_context(self, data: dict[str, Any]) -> str:
        """
        Format fetched data into human-readable context for the agent.

        The agent will receive this text prepended to the user's message.
        Use markdown formatting for readability.

        Args:
            data: The data dictionary from _fetch_data

        Returns:
            Formatted markdown string
        """
        # TODO: Format your data for the agent
        # Use clear sections and bullet points
        # Include emoji for visual clarity (optional)

        # Example format:
        return f"""
## 🎯 CONTEXTO: [Component Name]

**[Main Information]**
- Field 1: {data.get('field1', 'N/A')}
- Field 2: {data.get('field2', 'N/A')}

### 📊 [Section Name]
{self._format_list(['Item 1', 'Item 2', 'Item 3'])}

### 💡 [Another Section]
[More information here]

---

💡 *El usuario está viendo [component description]. Puedes responder preguntas sobre [what the agent can help with].*
"""

    # Helper methods (optional - add as needed)

    def _extract_parameter_from_message(self, message: str) -> str | None:
        """Extract a parameter from the user message using regex."""
        import re
        # Example: Extract ID from "ID: 12345"
        match = re.search(r"ID:\s*(\d+)", message, re.IGNORECASE)
        if match:
            return match.group(1)
        return None


# After creating this file:
# 1. Move it to tools/ directory:
#    mv _my_component.py tools/my_component.py
#
# 2. Import it in tools/__init__.py:
#    from .my_component import MyComponentTool
#    __all__ = [..., "MyComponentTool"]
#
# 3. Test registration:
#    python3 test_ui_tools.py
#
# 4. Use in frontend:
#    <ChateableWrapper uiComponent="my_component">
#      <YourComponent />
#    </ChateableWrapper>
