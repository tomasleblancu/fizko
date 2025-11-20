"""UI Tool for F29 Form Card component - Supabase version."""

from __future__ import annotations

import logging
from typing import Any

from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class F29FormCardTool(BaseUITool):
    """
    UI Tool for F29 Form Card component - Supabase version.

    When a user clicks or interacts with an F29 form card in the frontend,
    this tool provides context about the F29 form.
    """

    @property
    def component_name(self) -> str:
        return "f29_form_card"

    @property
    def description(self) -> str:
        return "Loads F29 form information when user views a form card"

    @property
    def domain(self) -> str:
        return "tax"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario ve una tarjeta de formulario F29."""
        return """
## 💡 INSTRUCCIONES: Tarjeta de Formulario F29

El usuario está viendo la ficha de un formulario F29 específico.

**Tu objetivo:**
- Responde preguntas sobre ESTE formulario F29 (detalles, estado, PDF)
- Ya se mostró el widget con el desglose del F29 arriba
- Sé breve y directo (máximo 2-3 líneas)

**Formato de respuesta:**
1. Saluda brevemente y menciona el período del F29
2. Pregunta qué le gustaría saber o hacer

**Evita:**
- Temas generales no relacionados con este formulario
- Respuestas largas
- Describir manualmente los números (ya están en el widget)
- **NO llames a herramientas adicionales**
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process F29 form card interaction and load relevant data."""

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        try:
            # Priority 1: Get form folio from entity_id (frontend UI component click)
            form_folio = context.additional_data.get("entity_id") if context.additional_data else None

            # Priority 2: Fallback to form_folio in additional_data
            if not form_folio:
                form_folio = context.additional_data.get("form_folio") if context.additional_data else None

            if not form_folio:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se especificó un folio de formulario",
                )

            # Format context text for agent
            context_text = f"""
## 📋 CONTEXTO: Formulario F29

**El usuario está viendo la ficha de un formulario F29 específico.**

**Folio**: {form_folio}

### 💡 INSTRUCCIONES:
- Ya se mostró el widget con el desglose del F29 arriba (si está disponible)
- Responde en máximo 2-3 líneas
- NO repitas la información del widget
- Pregunta qué le gustaría saber o hacer

**NOTA:** La información completa del F29 se cargará desde Supabase cuando esté disponible.
"""

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "form_folio": str(form_folio),
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing F29 form card: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar información del formulario F29: {str(e)}",
            )
