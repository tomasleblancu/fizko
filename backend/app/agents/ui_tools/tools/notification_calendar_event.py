"""UI Tool for Calendar Event Notification context - Supabase version."""

from __future__ import annotations

import logging
from typing import Any

from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class NotificationCalendarEventTool(BaseUITool):
    """
    UI Tool for Calendar Event Notifications.

    Loads enriched context when a user interacts with a notification about
    a calendar event (tax obligation). Works in both:
    - WhatsApp: When user responds to a notification
    - Web App: When user clicks on a notification in the chat

    Pre-loads:
    - Original notification details (when sent, message content)
    - Complete calendar event information (title, due date, status)
    - Event template details (category, authority)
    - Pending tasks with their status
    - Available actions user can take
    - Urgency level and days until due
    """

    @property
    def component_name(self) -> str:
        return "notification_calendar_event"

    @property
    def description(self) -> str:
        return "Loads calendar event notification context when user responds to tax obligation notification"

    @property
    def domain(self) -> str:
        return "notifications"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario responde a una notificación de calendario."""
        return """
## 💡 INSTRUCCIONES: Notificación de Evento Tributario

El usuario está respondiendo a una notificación que le enviamos sobre una obligación tributaria.

**Contexto importante:**
- La notificación fue enviada automáticamente según el calendario tributario
- El usuario espera ayuda específica con ESTE evento en particular
- Ya conoce la fecha de vencimiento porque se la informamos en la notificación

**Tu objetivo:**
- Ayuda al usuario con la obligación específica mencionada en la notificación
- Considera la **urgencia del vencimiento** (días restantes)
- Si hay tareas pendientes, enfócate en esas
- **NO llames herramientas adicionales** - toda la info está arriba

**Formato de respuesta:**
- Reconoce que viste su respuesta a la notificación
- Enfócate en los próximos pasos concretos que debe tomar
- Si el evento está próximo a vencer, resalta la urgencia
- Pregunta si necesita ayuda con alguna tarea específica

**Evita:**
- Repetir información que ya está en la notificación original
- Explicaciones largas sobre el tipo de obligación
- Hablar de otros eventos no relacionados
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """
        Process notification interaction and load calendar event context.

        Expects in additional_data:
        - notification_id: UUID of the notification in notification_history
        - entity_id: UUID of the calendar event (optional, loaded from notification if not provided)
        """

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        try:
            # Extract notification ID from additional_data
            notification_id = context.additional_data.get("notification_id") if context.additional_data else None

            if not notification_id:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se especificó el ID de la notificación",
                )

            # Get entity_id from additional_data
            entity_id = context.additional_data.get("entity_id") if context.additional_data else None

            # Format context text for agent
            context_text = self._format_notification_context(notification_id, entity_id)

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "notification_id": str(notification_id) if notification_id else None,
                    "event_id": str(entity_id) if entity_id else None,
                },
            )

        except Exception as e:
            self.logger.error(
                f"Error processing notification calendar event: {e}", exc_info=True
            )
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar contexto de notificación: {str(e)}",
            )

    def _format_notification_context(
        self,
        notification_id: str | None,
        event_id: str | None,
    ) -> str:
        """Format notification context into agent-readable text."""

        return f"""
## 📬 Contexto de Notificación de Calendario

**El usuario está respondiendo a una notificación sobre una obligación tributaria.**

### 💡 INSTRUCCIONES:
- El usuario respondió a una notificación automática del calendario tributario
- Ayúdalo con la obligación específica mencionada en la notificación
- Considera la urgencia del vencimiento si está disponible
- Enfócate en los próximos pasos concretos que debe tomar

**NOTA:** La información completa del evento se cargará desde Supabase cuando esté disponible.
"""
