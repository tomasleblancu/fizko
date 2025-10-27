"""UI Tool for Tax Calendar Event component."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ....db.models import CalendarEvent, CompanyEvent, EventHistory, EventTemplate
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class TaxCalendarEventTool(BaseUITool):
    """
    UI Tool for Tax Calendar Event component.

    When a user clicks on a calendar event (tax obligation) in the Tax Calendar,
    this tool pre-loads:
    - Event basic information (title, due date, status)
    - Event template details (category, authority, description)
    - Period information (period_start, period_end)
    - Company event configuration
    - Task information if available
    - Days until due date and urgency level

    This gives the agent immediate context about the tax obligation without
    needing to call additional tools.
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

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process tax calendar event interaction and load relevant data."""

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
            # Extract event ID from additional_data
            event_id = context.additional_data.get("entity_id")

            if not event_id:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se especificó el ID del evento tributario",
                )

            # Get calendar event data
            event_data = await self._get_calendar_event_data(
                context.db,
                context.company_id,
                event_id,
            )

            if not event_data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error=f"No se encontró el evento tributario con ID {event_id}",
                )

            # Format context text for agent
            context_text = self._format_event_context(event_data)

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=event_data,
                metadata={
                    "event_id": str(event_data.get("id")),
                    "event_title": event_data.get("title"),
                    "status": event_data.get("status"),
                    "category": event_data.get("category"),
                    "days_until": event_data.get("days_until"),
                    "urgency_level": event_data.get("urgency_level"),
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing tax calendar event: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar información del evento tributario: {str(e)}",
            )

    async def _get_calendar_event_data(
        self,
        db: AsyncSession,
        company_id: str,
        event_id: str,
    ) -> dict[str, Any] | None:
        """Fetch calendar event data from database with all related information."""

        company_uuid = self._safe_get_uuid(company_id)
        event_uuid = self._safe_get_uuid(event_id)

        if not company_uuid or not event_uuid:
            return None

        # Query calendar event with all relationships
        query = (
            select(CalendarEvent)
            .where(
                CalendarEvent.id == event_uuid,
                CalendarEvent.company_id == company_uuid,
            )
            .options(
                joinedload(CalendarEvent.event_template),
                joinedload(CalendarEvent.company_event),
                selectinload(CalendarEvent.tasks),
                selectinload(CalendarEvent.history),
            )
        )

        result = await db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            return None

        # Calculate days until due date
        days_until = self._calculate_days_until(event.due_date)
        urgency_level = self._get_urgency_level(days_until, event.status)

        # Format event data
        event_data = {
            "id": str(event.id),
            "title": event.title,
            "description": event.description,
            "due_date": event.due_date.isoformat() if event.due_date else None,
            "period_start": event.period_start.isoformat() if event.period_start else None,
            "period_end": event.period_end.isoformat() if event.period_end else None,
            "status": event.status,
            "completion_date": event.completion_date.isoformat() if event.completion_date else None,
            "completion_data": event.completion_data,
            "auto_generated": event.auto_generated,
            "days_until": days_until,
            "urgency_level": urgency_level,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "updated_at": event.updated_at.isoformat() if event.updated_at else None,
        }

        # Add event template information
        if event.event_template:
            template = event.event_template
            event_data["template"] = {
                "code": template.code,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "authority": template.authority,
                "is_mandatory": template.is_mandatory,
                "applies_to_regimes": template.applies_to_regimes,
            }
            event_data["category"] = template.category
            event_data["authority"] = template.authority

        # Add company event configuration
        if event.company_event:
            company_event = event.company_event
            event_data["company_event"] = {
                "is_active": company_event.is_active,
                "custom_config": company_event.custom_config,
            }

        # Add tasks information
        if event.tasks:
            event_data["tasks"] = [
                {
                    "id": str(task.id),
                    "task_type": task.task_type,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "order_index": task.order_index,
                    "is_automated": task.is_automated,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                }
                for task in sorted(event.tasks, key=lambda t: t.order_index)
            ]
            event_data["total_tasks"] = len(event.tasks)
            event_data["completed_tasks"] = sum(1 for task in event.tasks if task.status == "completed")
        else:
            event_data["tasks"] = []
            event_data["total_tasks"] = 0
            event_data["completed_tasks"] = 0

        # Add event history information
        if event.history:
            event_data["history"] = [
                {
                    "id": str(history.id),
                    "event_type": history.event_type,
                    "title": history.title,
                    "description": history.description,
                    "event_metadata": history.event_metadata,
                    "created_at": history.created_at.isoformat() if history.created_at else None,
                    "user_id": str(history.user_id) if history.user_id else None,
                }
                for history in sorted(event.history, key=lambda h: h.created_at, reverse=True)
            ]
            event_data["total_history_entries"] = len(event.history)
        else:
            event_data["history"] = []
            event_data["total_history_entries"] = 0

        return event_data

    def _calculate_days_until(self, due_date: date) -> int:
        """Calculate days until due date (negative if overdue)."""
        today = datetime.now().date()
        delta = due_date - today
        return delta.days

    def _get_urgency_level(self, days_until: int, status: str) -> str:
        """Determine urgency level based on days until and status."""
        if status == "completed":
            return "completed"
        if status == "overdue" or days_until < 0:
            return "overdue"
        if days_until == 0:
            return "due_today"
        if days_until <= 3:
            return "urgent"
        if days_until <= 7:
            return "soon"
        return "normal"

    def _format_event_context(self, event_data: dict[str, Any]) -> str:
        """Format calendar event data into human-readable context for agent."""

        # Status and urgency translations
        status_es = {
            "pending": "Pendiente",
            "in_progress": "En Progreso",
            "completed": "Completado",
            "overdue": "Vencido",
            "cancelled": "Cancelado",
        }.get(event_data["status"], event_data["status"])

        urgency_es = {
            "completed": "✅ Completado",
            "overdue": "🚨 VENCIDO",
            "due_today": "⚡ VENCE HOY",
            "urgent": "⚠️ Urgente",
            "soon": "📌 Próximo",
            "normal": "📅 Normal",
        }.get(event_data["urgency_level"], "📅 Normal")

        # Category translation
        category_es = {
            "impuesto_mensual": "💰 Impuesto Mensual",
            "impuesto_anual": "📊 Impuesto Anual",
            "prevision": "👥 Previsión",
            "declaracion_jurada": "📋 Declaración Jurada",
            "libros": "📚 Libros Contables",
            "otros": "📌 Otros",
        }.get(event_data.get("category", "otros"), "📌 Otros")

        lines = [
            "## 📅 CONTEXTO: Obligación Tributaria",
            "",
            f"**{event_data['title']}**",
            f"Estado: {status_es} | Urgencia: {urgency_es}",
            f"Categoría: {category_es}",
        ]

        # Due date information
        if event_data["due_date"]:
            due_date_str = datetime.fromisoformat(event_data["due_date"]).strftime("%d/%m/%Y")
            days_until = event_data["days_until"]

            if days_until < 0:
                lines.append(f"**Fecha de vencimiento: {due_date_str} (VENCIDO hace {abs(days_until)} días)**")
            elif days_until == 0:
                lines.append(f"**Fecha de vencimiento: {due_date_str} (VENCE HOY)**")
            else:
                lines.append(f"Fecha de vencimiento: {due_date_str} (Faltan {days_until} días)")

        # Period information
        if event_data.get("period_start") and event_data.get("period_end"):
            period_start = datetime.fromisoformat(event_data["period_start"]).strftime("%d/%m/%Y")
            period_end = datetime.fromisoformat(event_data["period_end"]).strftime("%d/%m/%Y")
            lines.append(f"Período: {period_start} - {period_end}")

        # Description
        if event_data.get("description"):
            lines.append("")
            lines.append(f"**Descripción:** {event_data['description']}")

        # Template information
        if template := event_data.get("template"):
            lines.append("")
            lines.append("### 📋 Información del Tipo de Obligación")
            lines.append(f"- **Código:** {template['code']}")
            if template.get("authority"):
                lines.append(f"- **Autoridad:** {template['authority']}")
            if template.get("description"):
                lines.append(f"- **Descripción:** {template['description']}")
            if template.get("is_mandatory"):
                lines.append("- **Obligatoriedad:** Obligatoria")

        # Tasks progress
        if event_data["total_tasks"] > 0:
            lines.append("")
            lines.append("### ✓ Tareas del Evento")
            completed = event_data["completed_tasks"]
            total = event_data["total_tasks"]
            progress_pct = (completed / total * 100) if total > 0 else 0
            lines.append(f"Progreso: {completed}/{total} tareas completadas ({progress_pct:.0f}%)")

            # List tasks
            for task in event_data["tasks"]:
                task_status = "✅" if task["status"] == "completed" else "⏳"
                lines.append(f"  {task_status} {task['title']}")

        # Completion information
        if event_data["status"] == "completed" and event_data.get("completion_date"):
            completion_date = datetime.fromisoformat(event_data["completion_date"]).strftime("%d/%m/%Y %H:%M")
            lines.append("")
            lines.append(f"**✅ Completado el:** {completion_date}")
            if completion_data := event_data.get("completion_data"):
                lines.append("**Datos de cumplimiento disponibles**")

        # Event History
        if event_data["total_history_entries"] > 0:
            lines.append("")
            lines.append("### 📜 Historial del Evento")
            lines.append(f"Total de registros: {event_data['total_history_entries']}")
            lines.append("")

            # Event type translations
            event_type_es = {
                "created": "🆕 Creado",
                "status_changed": "🔄 Cambio de estado",
                "note_added": "📝 Nota agregada",
                "document_attached": "📎 Documento adjunto",
                "task_completed": "✅ Tarea completada",
                "reminder_sent": "🔔 Recordatorio enviado",
                "updated": "📝 Actualizado",
                "completed": "✅ Completado",
                "cancelled": "❌ Cancelado",
                "system_action": "🤖 Acción automática",
            }

            # Show recent history (last 5 entries)
            recent_history = event_data["history"][:5]
            for history in recent_history:
                event_type = event_type_es.get(history["event_type"], history["event_type"])
                created_at = datetime.fromisoformat(history["created_at"]).strftime("%d/%m/%Y %H:%M")
                lines.append(f"- **{created_at}** - {event_type}: {history['title']}")
                if history.get("description"):
                    lines.append(f"  _{history['description']}_")

            if event_data["total_history_entries"] > 5:
                lines.append(f"  _... y {event_data['total_history_entries'] - 5} entradas más_")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("💡 **INSTRUCCIONES PARA EL AGENTE:**")
        lines.append("- Responde de forma **breve y directa** con la información clave de esta obligación tributaria")
        lines.append("- **NO llames a herramientas adicionales** para buscar este evento - toda la información necesaria ya está arriba")
        lines.append("- Si el usuario pregunta cómo cumplir con esta obligación, explica los pasos generales según el tipo de obligación")
        lines.append("- Si el usuario pregunta por el estado, explica claramente el estado actual y qué debe hacer")
        lines.append("- Termina tu respuesta preguntando al usuario si necesita ayuda para cumplir con esta obligación")
        lines.append("")

        return "\n".join(lines)
