"""UI Tool for Person Detail component - Supabase version."""

from __future__ import annotations

import logging
from typing import Any

from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class PersonDetailTool(BaseUITool):
    """
    UI Tool for Person Detail component - Supabase version.

    When a user clicks or interacts with a person card in the frontend,
    this tool provides context about the person/employee.
    """

    @property
    def component_name(self) -> str:
        return "person_detail"

    @property
    def description(self) -> str:
        return "Loads person/employee information when user views a person detail"

    @property
    def domain(self) -> str:
        return "payroll"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario ve detalles de un colaborador."""
        return """
## 💡 INSTRUCCIONES: Ficha de Colaborador

El usuario está viendo la información completa de un colaborador/empleado.

**Tu objetivo:**
- Responde preguntas sobre ESTE colaborador (sueldo, AFP, contrato, datos personales)
- Usa la información que ya está cargada arriba - **NO llames herramientas adicionales**
- Sé breve y directo (máximo 3-4 líneas)

**Formato de respuesta:**
- Inicia con un resumen clave del colaborador (cargo, estado, sueldo)
- Termina preguntando qué le gustaría hacer o saber sobre este colaborador

**Evita:**
- Temas generales sobre remuneraciones que no son específicos de este colaborador
- Buscar información que ya está en el contexto
- Explicaciones largas sobre conceptos de nómina
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process person detail interaction and load relevant data."""

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        try:
            # Get person_id from additional_data (passed from frontend click)
            person_id = context.additional_data.get("entity_id") if context.additional_data else None

            if not person_id:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se especificó un ID de persona",
                )

            # Format context text for agent
            context_text = f"""
## 👤 CONTEXTO: Información de Colaborador

**El usuario está viendo la ficha completa de un colaborador/empleado.**

### 💡 INSTRUCCIONES:
- El usuario seleccionó un colaborador específico
- Responde preguntas sobre este colaborador (sueldo, AFP, contrato, datos personales)
- Sé breve y directo (máximo 3-4 líneas)
- Termina preguntando qué le gustaría hacer o saber

**NOTA:** La información completa del colaborador se cargará desde Supabase cuando esté disponible.
"""

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "person_id": str(person_id),
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing person detail: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar información de la persona: {str(e)}",
            )
