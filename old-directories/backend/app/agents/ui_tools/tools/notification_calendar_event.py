"""UI Tool for Calendar Event Notification context."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import CalendarEvent, EventTask, NotificationHistory
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

            # Get entity_id from notification if not provided
            entity_id = (
                self._safe_get_uuid(context.additional_data.get("entity_id"))
                or notification.entity_id
            )

            if not entity_id:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="La notificación no tiene un evento de calendario asociado",
                )

            # Load calendar event with template
            event = await self._get_calendar_event(
                context.db, entity_id, context.company_id
            )

            if not event:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error=f"No se encontró el evento de calendario con ID {entity_id}",
                )

            # Load event tasks
            tasks = await self._get_event_tasks(context.db, entity_id)

            # Format context text for agent
            context_text = self._format_notification_context(
                notification=notification, event=event, tasks=tasks
            )

            # Calculate urgency metrics
            days_until_due = (event.due_date - date.today()).days
            is_urgent = days_until_due <= 1
            is_overdue = days_until_due < 0

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
                },
                "event": {
                    "id": str(event.id),
                    "title": event.event_template.name,
                    "description": event.event_template.description,
                    "due_date": event.due_date.isoformat(),
                    "status": event.status,
                    "days_until_due": days_until_due,
                    "is_urgent": is_urgent,
                    "is_overdue": is_overdue,
                    "template": {
                        "code": event.event_template.code,
                        "name": event.event_template.name,
                        "category": event.event_template.category,
                        "authority": event.event_template.authority,
                    },
                },
                "tasks": [
                    {
                        "id": str(task.id),
                        "title": task.title,
                        "description": task.description,
                        "status": task.status,
                        "order": task.order_index,
                    }
                    for task in tasks
                ],
                "tasks_summary": {
                    "total": len(tasks),
                    "pending": len([t for t in tasks if t.status == "pending"]),
                    "completed": len([t for t in tasks if t.status == "completed"]),
                },
                "actions": [
                    "mark_completed",
                    "view_tasks",
                    "postpone_event",
                    "view_documents",
                    "set_reminder",
                ],
            }

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=structured_data,
                metadata={
                    "notification_id": str(notification.id),
                    "event_id": str(event.id),
                    "urgency": "urgent" if is_urgent else "normal",
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

    async def _get_notification(
        self, db: AsyncSession, notification_id: UUID
    ) -> NotificationHistory | None:
        """Load notification from notification_history table."""
        stmt = select(NotificationHistory).where(
            NotificationHistory.id == notification_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_calendar_event(
        self, db: AsyncSession, event_id: UUID, company_id: str
    ) -> CalendarEvent | None:
        """Load calendar event with event template."""
        stmt = (
            select(CalendarEvent)
            .options(selectinload(CalendarEvent.event_template))
            .where(
                CalendarEvent.id == event_id,
                CalendarEvent.company_id == UUID(company_id),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_event_tasks(
        self, db: AsyncSession, event_id: UUID
    ) -> list[EventTask]:
        """Load tasks associated with the calendar event."""
        stmt = (
            select(EventTask)
            .where(EventTask.calendar_event_id == event_id)
            .order_by(EventTask.order_index)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    def _format_notification_context(
        self,
        notification: NotificationHistory,
        event: CalendarEvent,
        tasks: list[EventTask],
    ) -> str:
        """Format notification context into agent-readable text."""

        # Calculate urgency
        days_until = (event.due_date - date.today()).days
        if days_until < 0:
            urgency_text = f"⚠️ VENCIDO (hace {abs(days_until)} días)"
        elif days_until == 0:
            urgency_text = "⚠️ VENCE HOY"
        elif days_until == 1:
            urgency_text = "⚠️ VENCE MAÑANA"
        else:
            urgency_text = f"vence en {days_until} días"

        # Format notification time
        sent_time_str = notification.sent_at.strftime("%d/%m/%Y %H:%M")

        # Format tasks
        pending_tasks = [t for t in tasks if t.status != "completed"]
        completed_tasks = [t for t in tasks if t.status == "completed"]

        tasks_section = ""
        if tasks:
            tasks_list = []
            for task in tasks:
                status_icon = "✅" if task.status == "completed" else "⏳"
                tasks_list.append(f"{status_icon} {task.title} ({task.status})")
            tasks_section = (
                f"\n### Tareas ({len(completed_tasks)}/{len(tasks)} completadas)\n"
                + self._format_list(tasks_list)
            )

        # Format period if available
        period_str = "N/A"
        if event.period_start and event.period_end:
            period_str = f"{event.period_start.strftime('%m/%Y')} - {event.period_end.strftime('%m/%Y')}"
        elif event.period_start:
            period_str = event.period_start.strftime('%m/%Y')

        return f"""
## 📬 Contexto de Notificación de Calendario

**El usuario está respondiendo a una notificación sobre:**
**{event.event_template.name}**

### Información del Evento Tributario
- **Tipo:** {event.event_template.name} ({event.event_template.category})
- **Vencimiento:** {event.due_date.strftime('%d/%m/%Y')} ({urgency_text})
- **Estado actual:** {event.status}
- **Período:** {period_str}
- **Autoridad:** {event.event_template.authority}
- **Descripción:** {event.event_template.description or 'Sin descripción'}

### 📨 Notificación Enviada
- **Cuándo:** {sent_time_str}
- **Mensaje:** "{notification.message_content}"
- **Estado:** {notification.status}
- **Leído:** {"Sí" if notification.read_at else "No"}
{tasks_section}

### 🎯 Acciones Disponibles para el Usuario
{self._format_list([
    "Marcar evento como completado",
    "Ver detalle de tareas pendientes",
    "Posponer fecha de vencimiento",
    "Ver documentos relacionados",
    "Configurar recordatorio adicional"
])}
"""
