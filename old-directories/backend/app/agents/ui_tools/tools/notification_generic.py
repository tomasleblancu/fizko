"""UI Tool for Generic Notification context (fallback)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationHistory
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

        if not context.db:
            return UIToolResult(
                success=False,
                context_text="",
                error="Database session not available",
            )

        try:
            # Extract notification ID from additional_data
            notification_id = self._safe_get_uuid(
                context.additional_data.get("notification_id")
            )

            if not notification_id:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se especificó el ID de la notificación",
                )

            # Load notification from database
            notification = await self._get_notification(context.db, notification_id)

            if not notification:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error=f"No se encontró la notificación con ID {notification_id}",
                )

            # Format context text for agent
            context_text = self._format_notification_context(notification)

            # Build structured data
            structured_data = {
                "notification": {
                    "id": str(notification.id),
                    "sent_at": notification.sent_at.isoformat(),
                    "message": notification.message_content,
                    "status": notification.status,
                    "read_at": (
                        notification.read_at.isoformat() if notification.read_at else None
                    ),
                    "category": (
                        notification.notification_template.category
                        if notification.notification_template
                        else None
                    ),
                },
                "entity": {
                    "type": notification.entity_type,
                    "id": str(notification.entity_id) if notification.entity_id else None,
                }
                if notification.entity_type
                else None,
                "actions": [
                    "view_details",
                    "mark_as_read",
                    "get_help",
                ],
            }

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=structured_data,
                metadata={
                    "notification_id": str(notification.id),
                    "entity_type": notification.entity_type,
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

    async def _get_notification(
        self, db: AsyncSession, notification_id: UUID
    ) -> NotificationHistory | None:
        """Load notification from notification_history table."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(NotificationHistory)
            .options(selectinload(NotificationHistory.notification_template))
            .where(NotificationHistory.id == notification_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    def _format_notification_context(
        self, notification: NotificationHistory
    ) -> str:
        """Format generic notification context into agent-readable text."""

        # Format notification time
        sent_time_str = notification.sent_at.strftime("%d/%m/%Y %H:%M")

        # Get template info if available
        template_info = ""
        if notification.notification_template:
            template_info = f"\n- **Tipo:** {notification.notification_template.name} ({notification.notification_template.category})"

        # Get entity info if available
        entity_info = ""
        if notification.entity_type:
            entity_info = f"\n- **Relacionado con:** {notification.entity_type}"
            if notification.entity_id:
                entity_info += f" (ID: {notification.entity_id})"

        # Delivery status
        delivery_info = []
        if notification.delivered_at:
            delivery_info.append(
                f"Entregado: {notification.delivered_at.strftime('%d/%m/%Y %H:%M')}"
            )
        if notification.read_at:
            delivery_info.append(
                f"Leído: {notification.read_at.strftime('%d/%m/%Y %H:%M')}"
            )

        delivery_section = ""
        if delivery_info:
            delivery_section = "\n- " + "\n- ".join(delivery_info)

        return f"""
## 📬 Contexto de Notificación

**El usuario está respondiendo a una notificación enviada por el sistema.**

### Información de la Notificación
- **Enviada:** {sent_time_str}
- **Estado:** {notification.status}{template_info}{entity_info}{delivery_section}

### 📨 Mensaje Original
"{notification.message_content}"

### 🎯 Acciones Disponibles
{self._format_list([
    "Ver detalles completos",
    "Marcar como leído",
    "Obtener ayuda sobre este tema"
])}

**NOTA:** Esta es una notificación genérica. Para información más detallada sobre la entidad relacionada, considera usar una herramienta específica si está disponible.
"""
