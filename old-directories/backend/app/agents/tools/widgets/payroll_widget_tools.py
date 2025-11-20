"""Payroll Widget Tools - Interactive UI for person confirmation."""

from __future__ import annotations

import logging
from typing import Any

from agents import RunContextWrapper, function_tool

from ...core import FizkoContext
from .widgets import (
    create_person_confirmation_widget,
    person_confirmation_widget_copy_text,
)

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
async def show_person_confirmation(
    ctx: RunContextWrapper[FizkoContext],
    action: str,  # "create" or "update"
    first_name: str,
    last_name: str,
    rut: str,
    position_title: str | None = None,
    hire_date: str | None = None,  # ISO format YYYY-MM-DD
    base_salary: float | None = None,
    contract_type: str | None = None,  # indefinido, plazo_fijo, honorarios, por_obra, part_time
    email: str | None = None,
    phone: str | None = None,
    afp_provider: str | None = None,
    health_provider: str | None = None,
) -> dict[str, Any]:
    """
    Show a confirmation widget for creating or updating an employee.

    This tool MUST be called before actually creating or updating a person
    in the database. It displays all the information to the user and asks
    for confirmation.

    Args:
        action: "create" for new employee, "update" for existing employee
        first_name: Employee first name (required)
        last_name: Employee last name (required)
        rut: Employee RUT (required)
        position_title: Job title (optional)
        hire_date: Hire date in ISO format YYYY-MM-DD (optional)
        base_salary: Monthly base salary in CLP (optional)
        contract_type: Contract type - one of: indefinido, plazo_fijo, honorarios, por_obra, part_time (optional)
        email: Email address (optional)
        phone: Phone number (optional)
        afp_provider: AFP provider name (optional)
        health_provider: Health insurance provider name (optional)

    Returns:
        Success status and instructions for user

    Example:
        User: "Agregar a Juan Pérez, RUT 12345678-9, CEO, sueldo 3000000"
        Agent: show_person_confirmation(
            action="create",
            first_name="Juan",
            last_name="Pérez",
            rut="12345678-9",
            position_title="CEO",
            base_salary=3000000
        )
        Then WAIT for user response ("Confirmar" or "Cancelar")
    """
    try:
        # Create the widget
        widget = create_person_confirmation_widget(
            action=action,
            first_name=first_name,
            last_name=last_name,
            rut=rut,
            position_title=position_title,
            hire_date=hire_date,
            base_salary=base_salary,
            contract_type=contract_type,
            email=email,
            phone=phone,
            afp_provider=afp_provider,
            health_provider=health_provider,
        )

        # Generate copy text for accessibility / non-widget clients
        copy_text = person_confirmation_widget_copy_text(
            action=action,
            first_name=first_name,
            last_name=last_name,
            rut=rut,
            position_title=position_title,
            hire_date=hire_date,
            base_salary=base_salary,
            contract_type=contract_type,
            email=email,
            phone=phone,
            afp_provider=afp_provider,
            health_provider=health_provider,
        )

        if widget is None:
            logger.warning("Widgets not available, skipping")
            return {
                "success": False,
                "error": "Widgets not available",
            }

        # Stream the widget to the client
        await ctx.context.stream_widget(widget, copy_text=copy_text)

        logger.info(f"✅ Person confirmation widget streamed ({action}): {first_name} {last_name}")

        action_name = "crear" if action == "create" else "actualizar"
        return {
            "success": True,
            "message": f"Confirmación mostrada. Esperando respuesta del usuario para {action_name} a {first_name} {last_name}.",
            "next_steps": "Espera a que el usuario responda 'Confirmar' o 'Cancelar' antes de proceder.",
        }

    except Exception as e:
        logger.exception("Error creating person confirmation widget")
        return {
            "error": f"Error al mostrar confirmación: {str(e)}"
        }
