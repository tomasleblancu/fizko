"""UI Tool for Person Detail component."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Person
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class PersonDetailTool(BaseUITool):
    """
    UI Tool for Person Detail component.

    When a user clicks or interacts with a person card in the frontend,
    this tool pre-loads:
    - Person basic information (name, RUT, contact)
    - Position and contract details
    - Salary information
    - AFP and health insurance details
    - Bank account information
    - Employment status

    This gives the agent immediate context about the person without
    needing to call additional tools.
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
            # Get person_id from additional_data (passed from frontend click)
            person_id = context.additional_data.get("entity_id") if context.additional_data else None

            if not person_id:
                # Try to extract RUT from message
                person_rut = self._extract_rut_from_message(context.user_message)
                if person_rut:
                    person_data = await self._get_person_by_rut(
                        context.db,
                        context.company_id,
                        person_rut,
                    )
                else:
                    return UIToolResult(
                        success=False,
                        context_text="",
                        error="No se especificó un ID de persona ni un RUT",
                    )
            else:
                # Get person data by ID
                person_data = await self._get_person_by_id(
                    context.db,
                    context.company_id,
                    person_id,
                )

            if not person_data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error=f"No se encontró la persona con ID {person_id}" if person_id else "No se encontró la persona",
                )

            # Format context text for agent
            context_text = self._format_person_context(person_data)

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=person_data,
                metadata={
                    "person_id": person_data.get("id"),
                    "person_rut": person_data.get("rut"),
                    "status": person_data.get("status"),
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing person detail: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar información de la persona: {str(e)}",
            )

    async def _get_person_by_id(
        self,
        db: AsyncSession,
        company_id: str,
        person_id: str,
    ) -> dict[str, Any] | None:
        """Fetch person data from database by ID."""

        company_uuid = self._safe_get_uuid(company_id)
        person_uuid = self._safe_get_uuid(person_id)

        if not company_uuid or not person_uuid:
            return None

        query = select(Person).where(
            Person.company_id == company_uuid,
            Person.id == person_uuid
        )

        result = await db.execute(query)
        person = result.scalar_one_or_none()

        if not person:
            return None

        return self._format_person_data(person)

    async def _get_person_by_rut(
        self,
        db: AsyncSession,
        company_id: str,
        rut: str,
    ) -> dict[str, Any] | None:
        """Fetch person data from database by RUT."""

        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return None

        query = select(Person).where(
            Person.company_id == company_uuid,
            Person.rut == rut
        )

        result = await db.execute(query)
        person = result.scalar_one_or_none()

        if not person:
            return None

        return self._format_person_data(person)

    def _format_person_data(self, person: Person) -> dict[str, Any]:
        """Format person model into dict."""
        return {
            "id": str(person.id),
            "rut": person.rut,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "full_name": f"{person.first_name} {person.last_name}",
            "email": person.email,
            "phone": person.phone,
            "birth_date": person.birth_date.isoformat() if person.birth_date else None,
            "position_title": person.position_title,
            "contract_type": person.contract_type,
            "hire_date": person.hire_date.isoformat() if person.hire_date else None,
            "base_salary": float(person.base_salary) if person.base_salary else 0.0,
            "afp_provider": person.afp_provider,
            "afp_percentage": float(person.afp_percentage) if person.afp_percentage else None,
            "health_provider": person.health_provider,
            "health_plan": person.health_plan,
            "health_percentage": float(person.health_percentage) if person.health_percentage else None,
            "health_fixed_amount": float(person.health_fixed_amount) if person.health_fixed_amount else None,
            "bank_name": person.bank_name,
            "bank_account_type": person.bank_account_type,
            "bank_account_number": person.bank_account_number,
            "status": person.status,
            "termination_date": person.termination_date.isoformat() if person.termination_date else None,
            "termination_reason": person.termination_reason,
            "notes": person.notes,
            "photo_url": person.photo_url,
        }

    def _extract_rut_from_message(self, message: str) -> str | None:
        """Extract RUT from user message using common patterns."""
        import re

        # Pattern 1: "RUT: 12345678-9"
        match = re.search(r"RUT:?\s*([0-9]{7,8}-[0-9Kk])", message, re.IGNORECASE)
        if match:
            return match.group(1)

        # Pattern 2: Just the RUT "12345678-9"
        match = re.search(r"\b([0-9]{7,8}-[0-9Kk])\b", message)
        if match:
            return match.group(1)

        # Pattern 3: RUT without hyphen "123456789"
        match = re.search(r"\b([0-9]{8,9})\b", message)
        if match:
            rut = match.group(1)
            # Format: insert hyphen before last digit
            return f"{rut[:-1]}-{rut[-1]}"

        return None

    def _format_person_context(self, person_data: dict[str, Any]) -> str:
        """Format person data into human-readable context for agent."""

        status_es = {
            "active": "Activo",
            "inactive": "Inactivo",
            "terminated": "Desvinculado",
        }.get(person_data["status"], person_data["status"])

        lines = [
            "## 👤 CONTEXTO: Información de Colaborador",
            "",
            f"**{person_data['full_name']}**",
            f"RUT: {person_data['rut']}",
            f"Estado: {status_es}",
        ]

        # Contact info
        if person_data.get("email"):
            lines.append(f"Email: {person_data['email']}")
        if person_data.get("phone"):
            lines.append(f"Teléfono: {person_data['phone']}")

        # Position and contract
        lines.append("")
        lines.append("### 💼 Puesto y Contrato")

        if person_data.get("position_title"):
            lines.append(f"- **Cargo**: {person_data['position_title']}")

        if person_data.get("contract_type"):
            lines.append(f"- **Tipo de contrato**: {person_data['contract_type']}")

        if person_data.get("hire_date"):
            lines.append(f"- **Fecha de contratación**: {person_data['hire_date']}")

        # Salary
        lines.append("")
        lines.append("### 💰 Remuneración")
        lines.append(f"- **Sueldo base**: ${person_data['base_salary']:,.0f}")

        # AFP
        if person_data.get("afp_provider"):
            afp_text = f"- **AFP**: {person_data['afp_provider']}"
            if person_data.get("afp_percentage"):
                afp_text += f" ({person_data['afp_percentage']}%)"
            lines.append(afp_text)

        # Health
        if person_data.get("health_provider"):
            health_text = f"- **Salud**: {person_data['health_provider']}"
            if person_data.get("health_plan"):
                health_text += f" - {person_data['health_plan']}"
            if person_data.get("health_percentage"):
                health_text += f" ({person_data['health_percentage']}%)"
            elif person_data.get("health_fixed_amount"):
                health_text += f" (${person_data['health_fixed_amount']:,.0f})"
            lines.append(health_text)

        # Bank
        if person_data.get("bank_name"):
            lines.append("")
            lines.append("### 🏦 Datos Bancarios")
            bank_text = f"- **Banco**: {person_data['bank_name']}"
            if person_data.get("bank_account_type"):
                bank_text += f" - {person_data['bank_account_type']}"
            if person_data.get("bank_account_number"):
                bank_text += f" - {person_data['bank_account_number']}"
            lines.append(bank_text)

        # Termination info if applicable
        if person_data["status"] == "terminated" and person_data.get("termination_date"):
            lines.append("")
            lines.append("### 🚪 Desvinculación")
            lines.append(f"- **Fecha**: {person_data['termination_date']}")
            if person_data.get("termination_reason"):
                lines.append(f"- **Motivo**: {person_data['termination_reason']}")

        # Notes
        if person_data.get("notes"):
            lines.append("")
            lines.append("### 📝 Notas")
            lines.append(person_data["notes"])

        return "\n".join(lines)
