"""UI Tool for Tax Calendar Event component - Supabase version."""

from __future__ import annotations

import logging
from typing import Any

from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class TaxCalendarEventTool(BaseUITool):
    """
    UI Tool for Tax Calendar Event component - Supabase version.

    When a user clicks on a calendar event (tax obligation) in the Tax Calendar,
    this tool provides context to help the agent respond appropriately.
    """

    @property
    def component_name(self) -> str:
        return "tax_calendar_event"

    @property
    def description(self) -> str:
        return "Loads tax calendar event information when user clicks on a tax obligation"

    @property
    def domain(self) -> str:
        return "tax_calendar"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario ve un evento del calendario tributario."""
        return """
## 💡 INSTRUCCIONES: Evento del Calendario Tributario

El usuario está viendo los detalles de una obligación tributaria específica (F29, F50, etc.).

**Tu objetivo:**
- Responde de forma **breve y directa** sobre esta obligación específica
- **NO llames herramientas adicionales** para buscar este evento - toda la info ya está arriba
- Enfócate en el estado actual y próximos pasos

**Formato de respuesta:**
- Inicia con el estado de la obligación (pendiente, completada, próxima)
- Si pregunta cómo cumplir, explica los pasos generales según el tipo
- Termina preguntando si necesita ayuda para cumplir con esta obligación

**Evita:**
- Buscar información que ya está en el contexto
- Explicaciones largas sobre legislación tributaria
- Hablar de otras obligaciones no relacionadas con este evento
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process tax calendar event interaction and load relevant data."""

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        try:
            # Extract event ID from additional_data
            event_id = context.additional_data.get("entity_id") if context.additional_data else None

            if not event_id:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se especificó el ID del evento tributario",
                )

            # Format context text for agent
            context_text = f"""
## 📅 CONTEXTO: Obligación Tributaria

**El usuario está viendo los detalles de una obligación tributaria del calendario.**

### 💡 INSTRUCCIONES:
- El usuario seleccionó un evento específico del calendario tributario
- Enfócate en el estado actual y próximos pasos para esta obligación
- Si pregunta cómo cumplir, explica los pasos generales según el tipo de obligación
- Responde de forma breve y directa

**NOTA:** La información completa del evento se cargará desde Supabase cuando esté disponible.
"""

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "event_id": str(event_id),
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing tax calendar event: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar información del evento tributario: {str(e)}",
            )
