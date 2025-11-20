"""Tools for Payroll Agent - Employee/collaborator management and labor law support.

Main tools:
1. get_people() - List all employees
2. get_person() - Get specific employee details
3. create_person() - Register new employee
4. update_person() - Update employee information
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import date

from agents import RunContextWrapper, function_tool

from app.agents.core import FizkoContext
from app.agents.tools.utils import get_supabase
from app.utils.rut import normalize_rut, validate_rut
from app.agents.tools.decorators import require_subscription_tool

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
@require_subscription_tool("get_people")
async def get_people(
    ctx: RunContextWrapper[FizkoContext],
    limit: int = 50,
) -> dict[str, Any]:
    """
    List all employees/collaborators of the company.

    Args:
        limit: Maximum number of employees to return (default 50, max 100)

    Returns:
        List of employees with basic information (name, RUT, position, status)

    Example:
        - List all: get_people()
        - List first 10: get_people(limit=10)
    """
    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    try:
        supabase = get_supabase()

        # Limit to max 100
        limit = min(limit, 100)

        people = await supabase.people.get_people_by_company(
            company_id=company_id,
            limit=limit
        )

        return {
            "total_count": len(people),
            "limit": limit,
            "people": [
                {
                    "id": person.get("id"),
                    "rut": person.get("rut"),
                    "full_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                    "position": person.get("position_title"),
                    "status": person.get("status"),
                    "hire_date": person.get("hire_date"),
                    "email": person.get("email"),
                    "phone": person.get("phone"),
                }
                for person in people
            ],
        }

    except Exception as e:
        logger.exception("Error fetching people")
        return {"error": f"Error al obtener colaboradores: {str(e)}"}


@function_tool(strict_mode=False)
async def get_person(
    ctx: RunContextWrapper[FizkoContext],
    person_id: str | None = None,
    rut: str | None = None,
) -> dict[str, Any]:
    """
    Get detailed information about a specific employee.

    You must provide either person_id OR rut.

    Args:
        person_id: Employee UUID (optional)
        rut: Employee RUT in any format (optional, will be normalized)

    Returns:
        Complete employee information including personal data, contract, and salary details

    Examples:
        - By ID: get_person(person_id="123e4567-...")
        - By RUT: get_person(rut="12345678-9")
    """
    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    if not person_id and not rut:
        return {"error": "Debes proporcionar person_id o rut"}

    try:
        supabase = get_supabase()

        # Fetch person
        if person_id:
            person = await supabase.people.get_person_by_id(person_id)
        else:
            normalized_rut = normalize_rut(rut)
            person = await supabase.people.get_person_by_rut(company_id, normalized_rut)

        if not person:
            return {"error": "Colaborador no encontrado"}

        # Helper to safely convert to float
        def to_float(value):
            if value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        return {
            "person": {
                "id": person.get("id"),
                # Personal Information
                "rut": person.get("rut"),
                "first_name": person.get("first_name"),
                "last_name": person.get("last_name"),
                "full_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "email": person.get("email"),
                "phone": person.get("phone"),
                "birth_date": person.get("birth_date"),
                # Position and Contract
                "position_title": person.get("position_title"),
                "contract_type": person.get("contract_type"),
                "hire_date": person.get("hire_date"),
                # Salary Information
                "base_salary": to_float(person.get("base_salary")),
                # AFP (Pension)
                "afp_provider": person.get("afp_provider"),
                "afp_percentage": to_float(person.get("afp_percentage")),
                # Health Insurance
                "health_provider": person.get("health_provider"),
                "health_plan": person.get("health_plan"),
                "health_percentage": to_float(person.get("health_percentage")),
                "health_fixed_amount": to_float(person.get("health_fixed_amount")),
                # Bank Information
                "bank_name": person.get("bank_name"),
                "bank_account_type": person.get("bank_account_type"),
                "bank_account_number": person.get("bank_account_number"),
                # Employment Status
                "status": person.get("status"),
                "termination_date": person.get("termination_date"),
                "termination_reason": person.get("termination_reason"),
                # Additional
                "notes": person.get("notes"),
                "photo_url": person.get("photo_url"),
                "created_at": person.get("created_at"),
                "updated_at": person.get("updated_at"),
            }
        }

    except Exception as e:
        logger.exception("Error fetching person")
        return {"error": f"Error al obtener colaborador: {str(e)}"}


@function_tool(strict_mode=False)
@require_subscription_tool("create_person")
async def create_person(
    ctx: RunContextWrapper[FizkoContext],
    # Personal Information (REQUIRED)
    rut: str,
    first_name: str,
    last_name: str,
    # Personal Information (OPTIONAL)
    email: str | None = None,
    phone: str | None = None,
    birth_date: str | None = None,  # Format: YYYY-MM-DD
    # Position and Contract
    position_title: str | None = None,
    contract_type: str | None = None,  # Options: indefinido, plazo_fijo, honorarios, por_obra, part_time
    hire_date: str | None = None,  # Format: YYYY-MM-DD
    # Salary Information
    base_salary: float = 0.0,
    # AFP (Pension)
    afp_provider: str | None = None,
    afp_percentage: float | None = 10.49,
    # Health Insurance
    health_provider: str | None = None,
    health_plan: str | None = None,
    health_percentage: float | None = None,
    health_fixed_amount: float | None = None,
    # Bank Information
    bank_name: str | None = None,
    bank_account_type: str | None = None,
    bank_account_number: str | None = None,
    # Additional
    notes: str | None = None,
    photo_url: str | None = None,
) -> dict[str, Any]:
    """
    Create a new employee/collaborator.

    Required fields:
    - rut: Employee RUT (will be validated and normalized)
    - first_name: First name
    - last_name: Last name

    Optional fields:
    - All other fields are optional

    Contract types: indefinido, plazo_fijo, honorarios, por_obra, part_time

    Args:
        See parameter descriptions above

    Returns:
        Created employee information with ID

    Example:
        create_person(
            rut="12345678-9",
            first_name="Juan",
            last_name="Pérez",
            position_title="Contador",
            hire_date="2025-01-01",
            base_salary=800000
        )
    """
    from app.db.models import Person

    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    # Validate RUT
    normalized_rut = normalize_rut(rut)
    if not validate_rut(normalized_rut):
        return {"error": f"RUT inválido: {rut}"}

    try:
        supabase = get_supabase()

        # Check if person with this RUT already exists
        existing = await supabase.people.get_person_by_rut(company_id, normalized_rut)
        if existing:
            return {"error": f"Ya existe un colaborador con RUT {normalized_rut}"}

        # Create person with all fields
        person_data = {
            "email": email,
            "phone": phone,
            "birth_date": birth_date,
            "position_title": position_title,
            "contract_type": contract_type,
            "hire_date": hire_date,
            "base_salary": base_salary,
            "afp_provider": afp_provider,
            "afp_percentage": afp_percentage,
            "health_provider": health_provider,
            "health_plan": health_plan,
            "health_percentage": health_percentage,
            "health_fixed_amount": health_fixed_amount,
            "bank_name": bank_name,
            "bank_account_type": bank_account_type,
            "bank_account_number": bank_account_number,
            "notes": notes,
            "photo_url": photo_url,
        }

        person = await supabase.people.create(
            company_id=company_id,
            rut=normalized_rut,
            first_name=first_name,
            last_name=last_name,
            **person_data
        )

        if not person:
            return {"error": "Error al crear colaborador"}

        full_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()

        return {
            "success": True,
            "message": f"Colaborador {full_name} creado exitosamente",
            "person": {
                "id": person.get("id"),
                "rut": person.get("rut"),
                "full_name": full_name,
                "position": person.get("position_title"),
                "hire_date": person.get("hire_date"),
                "base_salary": float(person.get("base_salary", 0)),
            }
        }

    except ValueError as e:
        return {"error": f"Error en formato de datos: {str(e)}"}
    except Exception as e:
        logger.exception("Error creating person")
        return {"error": f"Error al crear colaborador: {str(e)}"}


@function_tool(strict_mode=False)
@require_subscription_tool("update_person")
async def update_person(
    ctx: RunContextWrapper[FizkoContext],
    person_id: str,
    # Personal Information
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    birth_date: str | None = None,  # Format: YYYY-MM-DD
    # Position and Contract
    position_title: str | None = None,
    contract_type: str | None = None,
    hire_date: str | None = None,  # Format: YYYY-MM-DD
    # Salary Information
    base_salary: float | None = None,
    # AFP
    afp_provider: str | None = None,
    afp_percentage: float | None = None,
    # Health
    health_provider: str | None = None,
    health_plan: str | None = None,
    health_percentage: float | None = None,
    health_fixed_amount: float | None = None,
    # Bank
    bank_name: str | None = None,
    bank_account_type: str | None = None,
    bank_account_number: str | None = None,
    # Status
    status: str | None = None,  # Options: active, inactive, terminated
    termination_date: str | None = None,  # Format: YYYY-MM-DD
    termination_reason: str | None = None,
    # Additional
    notes: str | None = None,
    photo_url: str | None = None,
) -> dict[str, Any]:
    """
    Update employee information.

    Only the fields you provide will be updated. All fields are optional.

    Args:
        person_id: Employee UUID (required)
        All other fields are optional - only provided fields will be updated

    Returns:
        Updated employee information

    Example:
        update_person(
            person_id="123e4567-...",
            base_salary=900000,
            position_title="Contador Senior"
        )
    """
    from app.db.models import Person

    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    try:
        supabase = get_supabase()

        # Fetch person to verify it exists and belongs to company
        person = await supabase.people.get_person_by_id(person_id)
        if not person or person.get("company_id") != company_id:
            return {"error": "Colaborador no encontrado"}

        # Build update dict with only provided fields
        update_data = {}
        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name
        if email is not None:
            update_data["email"] = email
        if phone is not None:
            update_data["phone"] = phone
        if birth_date is not None:
            update_data["birth_date"] = birth_date
        if position_title is not None:
            update_data["position_title"] = position_title
        if contract_type is not None:
            update_data["contract_type"] = contract_type
        if hire_date is not None:
            update_data["hire_date"] = hire_date
        if base_salary is not None:
            update_data["base_salary"] = base_salary
        if afp_provider is not None:
            update_data["afp_provider"] = afp_provider
        if afp_percentage is not None:
            update_data["afp_percentage"] = afp_percentage
        if health_provider is not None:
            update_data["health_provider"] = health_provider
        if health_plan is not None:
            update_data["health_plan"] = health_plan
        if health_percentage is not None:
            update_data["health_percentage"] = health_percentage
        if health_fixed_amount is not None:
            update_data["health_fixed_amount"] = health_fixed_amount
        if bank_name is not None:
            update_data["bank_name"] = bank_name
        if bank_account_type is not None:
            update_data["bank_account_type"] = bank_account_type
        if bank_account_number is not None:
            update_data["bank_account_number"] = bank_account_number
        if status is not None:
            update_data["status"] = status
        if termination_date is not None:
            update_data["termination_date"] = termination_date
        if termination_reason is not None:
            update_data["termination_reason"] = termination_reason
        if notes is not None:
            update_data["notes"] = notes
        if photo_url is not None:
            update_data["photo_url"] = photo_url

        # Update person
        updated_person = await supabase.people.update(person_id, **update_data)
        if not updated_person:
            return {"error": "Error al actualizar colaborador"}

        full_name = f"{updated_person.get('first_name', '')} {updated_person.get('last_name', '')}".strip()

        return {
            "success": True,
            "message": f"Colaborador {full_name} actualizado exitosamente",
            "person": {
                "id": updated_person.get("id"),
                "rut": updated_person.get("rut"),
                "full_name": full_name,
                "position": updated_person.get("position_title"),
                "status": updated_person.get("status"),
                "base_salary": float(updated_person.get("base_salary", 0)),
            }
        }

    except ValueError as e:
        return {"error": f"Error en formato de datos: {str(e)}"}
    except Exception as e:
        logger.exception("Error updating person")
        return {"error": f"Error al actualizar colaborador: {str(e)}"}
