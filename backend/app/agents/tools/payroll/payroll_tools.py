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
from uuid import UUID

from agents import RunContextWrapper, function_tool
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.config.database import AsyncSessionLocal
from app.agents.core import FizkoContext
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
    from app.db.models import Person

    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    try:
        async with AsyncSessionLocal() as session:
            # Limit to max 100
            limit = min(limit, 100)

            stmt = (
                select(Person)
                .where(Person.company_id == UUID(company_id))
                .order_by(Person.last_name, Person.first_name)
                .limit(limit)
            )

            result = await session.execute(stmt)
            people = result.scalars().all()

            return {
                "total_count": len(people),
                "limit": limit,
                "people": [
                    {
                        "id": str(person.id),
                        "rut": person.rut,
                        "full_name": person.full_name,
                        "position": person.position_title,
                        "status": person.status,
                        "hire_date": person.hire_date.isoformat() if person.hire_date else None,
                        "email": person.email,
                        "phone": person.phone,
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
    from app.db.models import Person

    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    if not person_id and not rut:
        return {"error": "Debes proporcionar person_id o rut"}

    try:
        async with AsyncSessionLocal() as session:
            # Build query
            conditions = [Person.company_id == UUID(company_id)]

            if person_id:
                conditions.append(Person.id == UUID(person_id))
            elif rut:
                normalized_rut = normalize_rut(rut)
                conditions.append(Person.rut == normalized_rut)

            stmt = select(Person).where(*conditions)
            result = await session.execute(stmt)
            person = result.scalar_one_or_none()

            if not person:
                return {"error": "Colaborador no encontrado"}

            return {
                "person": {
                    "id": str(person.id),
                    # Personal Information
                    "rut": person.rut,
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                    "full_name": person.full_name,
                    "email": person.email,
                    "phone": person.phone,
                    "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                    # Position and Contract
                    "position_title": person.position_title,
                    "contract_type": person.contract_type,
                    "hire_date": person.hire_date.isoformat() if person.hire_date else None,
                    # Salary Information
                    "base_salary": float(person.base_salary),
                    # AFP (Pension)
                    "afp_provider": person.afp_provider,
                    "afp_percentage": float(person.afp_percentage) if person.afp_percentage else None,
                    # Health Insurance
                    "health_provider": person.health_provider,
                    "health_plan": person.health_plan,
                    "health_percentage": float(person.health_percentage) if person.health_percentage else None,
                    "health_fixed_amount": float(person.health_fixed_amount) if person.health_fixed_amount else None,
                    # Bank Information
                    "bank_name": person.bank_name,
                    "bank_account_type": person.bank_account_type,
                    "bank_account_number": person.bank_account_number,
                    # Employment Status
                    "status": person.status,
                    "termination_date": person.termination_date.isoformat() if person.termination_date else None,
                    "termination_reason": person.termination_reason,
                    # Additional
                    "notes": person.notes,
                    "photo_url": person.photo_url,
                    "created_at": person.created_at.isoformat(),
                    "updated_at": person.updated_at.isoformat(),
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
        async with AsyncSessionLocal() as session:
            # Check if person with this RUT already exists
            existing_stmt = select(Person).where(
                Person.company_id == UUID(company_id),
                Person.rut == normalized_rut
            )
            existing_result = await session.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                return {"error": f"Ya existe un colaborador con RUT {normalized_rut}"}

            # Parse dates
            birth_date_obj = date.fromisoformat(birth_date) if birth_date else None
            hire_date_obj = date.fromisoformat(hire_date) if hire_date else None

            # Create person
            person = Person(
                company_id=UUID(company_id),
                # Personal Information
                rut=normalized_rut,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                birth_date=birth_date_obj,
                # Position and Contract
                position_title=position_title,
                contract_type=contract_type,
                hire_date=hire_date_obj,
                # Salary Information
                base_salary=base_salary,
                # AFP
                afp_provider=afp_provider,
                afp_percentage=afp_percentage,
                # Health
                health_provider=health_provider,
                health_plan=health_plan,
                health_percentage=health_percentage,
                health_fixed_amount=health_fixed_amount,
                # Bank
                bank_name=bank_name,
                bank_account_type=bank_account_type,
                bank_account_number=bank_account_number,
                # Additional
                notes=notes,
                photo_url=photo_url,
                status="active",
            )

            session.add(person)
            await session.commit()
            await session.refresh(person)

            return {
                "success": True,
                "message": f"Colaborador {person.full_name} creado exitosamente",
                "person": {
                    "id": str(person.id),
                    "rut": person.rut,
                    "full_name": person.full_name,
                    "position": person.position_title,
                    "hire_date": person.hire_date.isoformat() if person.hire_date else None,
                    "base_salary": float(person.base_salary),
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
        async with AsyncSessionLocal() as session:
            # Fetch person
            stmt = select(Person).where(
                Person.company_id == UUID(company_id),
                Person.id == UUID(person_id)
            )
            result = await session.execute(stmt)
            person = result.scalar_one_or_none()

            if not person:
                return {"error": "Colaborador no encontrado"}

            # Update fields (only if provided)
            if first_name is not None:
                person.first_name = first_name
            if last_name is not None:
                person.last_name = last_name
            if email is not None:
                person.email = email
            if phone is not None:
                person.phone = phone
            if birth_date is not None:
                person.birth_date = date.fromisoformat(birth_date)
            if position_title is not None:
                person.position_title = position_title
            if contract_type is not None:
                person.contract_type = contract_type
            if hire_date is not None:
                person.hire_date = date.fromisoformat(hire_date)
            if base_salary is not None:
                person.base_salary = base_salary
            if afp_provider is not None:
                person.afp_provider = afp_provider
            if afp_percentage is not None:
                person.afp_percentage = afp_percentage
            if health_provider is not None:
                person.health_provider = health_provider
            if health_plan is not None:
                person.health_plan = health_plan
            if health_percentage is not None:
                person.health_percentage = health_percentage
            if health_fixed_amount is not None:
                person.health_fixed_amount = health_fixed_amount
            if bank_name is not None:
                person.bank_name = bank_name
            if bank_account_type is not None:
                person.bank_account_type = bank_account_type
            if bank_account_number is not None:
                person.bank_account_number = bank_account_number
            if status is not None:
                person.status = status
            if termination_date is not None:
                person.termination_date = date.fromisoformat(termination_date)
            if termination_reason is not None:
                person.termination_reason = termination_reason
            if notes is not None:
                person.notes = notes
            if photo_url is not None:
                person.photo_url = photo_url

            await session.commit()
            await session.refresh(person)

            return {
                "success": True,
                "message": f"Colaborador {person.full_name} actualizado exitosamente",
                "person": {
                    "id": str(person.id),
                    "rut": person.rut,
                    "full_name": person.full_name,
                    "position": person.position_title,
                    "status": person.status,
                    "base_salary": float(person.base_salary),
                }
            }

    except ValueError as e:
        return {"error": f"Error en formato de datos: {str(e)}"}
    except Exception as e:
        logger.exception("Error updating person")
        return {"error": f"Error al actualizar colaborador: {str(e)}"}
