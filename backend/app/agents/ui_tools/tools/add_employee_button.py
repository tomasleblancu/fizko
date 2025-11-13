"""UI Tool for Add Employee Button component."""

from __future__ import annotations

import logging

from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class AddEmployeeButtonTool(BaseUITool):
    """
    UI Tool for Add Employee Button component.

    When a user clicks the "Add Employee" button in the frontend,
    this tool provides context to the agent indicating that the user
    wants to start the employee creation flow immediately.

    This prevents the agent from showing a list of existing employees
    and instead starts directly with the employee creation workflow.
    """

    @property
    def component_name(self) -> str:
        return "add_employee_button"

    @property
    def description(self) -> str:
        return "Handles employee creation intent when user clicks Add Employee button"

    @property
    def domain(self) -> str:
        return "payroll"

    @property
    def agent_instructions(self) -> str:
        """Instructions for handling add employee button click."""
        return "El usuario hizo clic en el botón 'Agregar Empleado'."

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process add employee button click."""

        try:
            context_text = "El usuario hizo clic en el botón 'Agregar Empleado'."

            logger.info(f"✅ Add employee button clicked for company {context.company_id}")

            return UIToolResult(
                success=True,
                context_text=context_text,
            )

        except Exception as e:
            logger.exception("Error processing add employee button context")
            return UIToolResult(
                success=False,
                context_text="",
                error=str(e),
            )
