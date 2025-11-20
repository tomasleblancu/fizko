"""UI Tool for Generic Notification context (fallback) - Supabase version."""

from __future__ import annotations

import logging
from typing import Any

from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class NotificationGenericTool(BaseUITool):
    """
    Generic UI Tool for Notifications (fallback).

    This tool handles notifications that don't have a specialized tool yet.
    It loads basic notification information without deep entity context.

    Use cases:
    - New notification types without dedicated tools
    - System notifications without entities
    - Fallback when specific tool fails

    Pre-loads:
    - Notification details (when sent, message, status)
    - Basic entity information if available (type and ID only)
    - Generic available actions
    """

    @property
    def component_name(self) -> str:
        return "notification_generic"

    @property
    def description(self) -> str:
        return "Generic notification context loader (fallback for notifications without specific tools)"

    @property
    def domain(self) -> str:
        return "notifications"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario responde a una notificación genérica."""
        return """
## 💡 INSTRUCCIONES: Notificación Genérica

El usuario está respondiendo a una notificación del sistema (no tiene un tool especializado).

**Tu objetivo:**
- Ayuda al usuario con el tema mencionado en la notificación
- Considera que el usuario ya recibió información básica en la notificación
- Si la notificación menciona una entidad específica (documento, evento), enfócate en eso

**Formato de respuesta:**
- Reconoce que viste su respuesta a la notificación
- Ofrece ayuda específica según el tipo de notificación
- Pregunta qué necesita o qué acción quiere tomar

**Evita:**
- Repetir exactamente lo que decía la notificación
- Hablar de temas no relacionados con la notificación
- Asumir contexto que no está en la información cargada

**NOTA:** Esta es una notificación genérica. Si tiene entity_type y entity_id, puedes ofrecer ver más detalles usando herramientas específicas si el usuario lo solicita.
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """
        Process generic notification interaction.

        Expects in additional_data:
        - notification_id: UUID of the notification in notification_history
        """

        try:
            # Extract notification ID from additional_data
            notification_id = context.additional_data.get("notification_id") if context.additional_data else None

            if not notification_id:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se especificó el ID de la notificación",
                )

            # Format context text for agent
            context_text = self._format_notification_context(notification_id)

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "notification_id": str(notification_id),
                },
            )

        except Exception as e:
            self.logger.error(
                f"Error processing generic notification: {e}", exc_info=True
            )
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar contexto de notificación: {str(e)}",
            )

    def _format_notification_context(self, notification_id: str) -> str:
        """Format generic notification context into agent-readable text."""

        return f"""
## 📬 Contexto de Notificación

**El usuario está respondiendo a una notificación enviada por el sistema.**

### 💡 INSTRUCCIONES:
- Ayuda al usuario con el tema mencionado en la notificación
- El usuario ya recibió información básica en la notificación
- Ofrece ayuda específica según el tipo de notificación
- Pregunta qué necesita o qué acción quiere tomar

**NOTA:** La información completa de la notificación se cargará desde Supabase cuando esté disponible.
"""
