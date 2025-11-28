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

            # Load event from Supabase with template and tasks
            event = await context.supabase.calendar.get_event_by_id(
                event_id=str(event_id),
                include_template=True,
                include_tasks=True,
                include_history=False
            )

            if not event:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error=f"No se encontró el evento con ID: {event_id}",
                )

            # Extract event data
            template = event.get("event_templates", {})
            template_name = template.get("name", "Obligación tributaria")
            template_code = template.get("code", "unknown")
            template_description = template.get("description", "")

            due_date = event.get("due_date", "")
            period_start = event.get("period_start", "")
            period_end = event.get("period_end", "")
            status = event.get("status", "pending")

            # Status translations
            status_map = {
                "pending": "⏳ Pendiente",
                "in_progress": "🔄 En progreso",
                "completed": "✅ Completada",
                "overdue": "⚠️ Vencida",
                "cancelled": "❌ Cancelada"
            }
            status_text = status_map.get(status, status)

            # Tasks if available
            tasks = event.get("event_tasks", [])
            tasks_text = ""
            if tasks:
                tasks_text = "\n\n### 📋 Tareas relacionadas:\n"
                for idx, task in enumerate(tasks[:5], 1):  # Limit to 5 tasks
                    task_title = task.get("title", "Sin título")
                    task_status = task.get("status", "pending")
                    task_emoji = "✅" if task_status == "completed" else "⬜"
                    tasks_text += f"{idx}. {task_emoji} {task_title}\n"

            # Format context text for agent
            context_text = f"""
## 📅 CONTEXTO: {template_name}

**El usuario está viendo los detalles de esta obligación tributaria específica.**

### 📊 Información del evento:
- **Tipo**: {template_name} ({template_code})
- **Estado**: {status_text}
- **Fecha de vencimiento**: {due_date}
- **Periodo tributario**: {period_start} al {period_end}

{f"**Descripción**: {template_description}" if template_description else ""}
{tasks_text}

### 💡 INSTRUCCIONES PARA EL AGENTE:
- **NO llames herramientas adicionales** para buscar este evento - toda la información ya está arriba
- Enfócate en el estado actual y próximos pasos para esta obligación específica
- Si pregunta cómo cumplir, explica los pasos generales según el tipo de obligación ({template_code})
- Responde de forma **breve y directa**
- Si el estado es "completada", confirma que ya fue cumplida
- Si el estado es "vencida", menciona que está fuera de plazo y sugiere regularizar
- Si el estado es "pendiente", indica los pasos para cumplirla antes del vencimiento
""".strip()

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "event_id": str(event_id),
                    "template_code": template_code,
                    "status": status,
                    "due_date": due_date,
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing tax calendar event: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar información del evento tributario: {str(e)}",
            )
