"""Tools for Remuneraciones Agent - Chilean payroll calculations."""

from __future__ import annotations

import logging
from typing import Any
from decimal import Decimal

from agents import RunContextWrapper, function_tool

from app.agents.core import FizkoContext

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
async def calculate_salary(
    ctx: RunContextWrapper[FizkoContext],
    base_salary: float,
    bonuses: float = 0,
    overtime: float = 0,
    afp_rate: float = 10.0,
    health_rate: float = 7.0,
) -> dict[str, Any]:
    """
    Calculate net salary with standard Chilean deductions.

    Args:
        base_salary: Base monthly salary
        bonuses: Additional bonuses
        overtime: Overtime pay
        afp_rate: AFP contribution rate (default 10%)
        health_rate: Health contribution rate (default 7%)

    Returns:
        Detailed salary calculation breakdown
    """
    # Calculate gross salary
    gross = Decimal(str(base_salary)) + Decimal(str(bonuses)) + Decimal(str(overtime))

    # Calculate deductions
    afp_contribution = gross * (Decimal(str(afp_rate)) / Decimal("100"))
    health_contribution = gross * (Decimal(str(health_rate)) / Decimal("100"))

    # Unemployment insurance (employee): 0.6%
    unemployment_employee = gross * Decimal("0.006")

    # Income tax (simplified - actual calculation is more complex)
    # This is a simplified estimate based on income brackets
    taxable_income = gross
    income_tax = Decimal("0")

    # Chilean tax brackets (2024 simplified)
    if taxable_income > Decimal("4716960"):  # ~13.5 UF
        income_tax = (taxable_income - Decimal("4716960")) * Decimal("0.04")

    # Total deductions
    total_deductions = afp_contribution + health_contribution + unemployment_employee + income_tax

    # Net salary
    net_salary = gross - total_deductions

    return {
        "gross_salary": float(gross.quantize(Decimal("0.01"))),
        "deductions": {
            "afp": float(afp_contribution.quantize(Decimal("0.01"))),
            "health": float(health_contribution.quantize(Decimal("0.01"))),
            "unemployment_insurance": float(unemployment_employee.quantize(Decimal("0.01"))),
            "income_tax": float(income_tax.quantize(Decimal("0.01"))),
            "total": float(total_deductions.quantize(Decimal("0.01"))),
        },
        "net_salary": float(net_salary.quantize(Decimal("0.01"))),
        "breakdown": {
            "base_salary": base_salary,
            "bonuses": bonuses,
            "overtime": overtime,
        },
    }


@function_tool(strict_mode=False)
async def calculate_employer_contributions(
    ctx: RunContextWrapper[FizkoContext],
    base_salary: float,
) -> dict[str, Any]:
    """
    Calculate employer contributions (employer's cost beyond salary).

    Args:
        base_salary: Employee's base salary

    Returns:
        Breakdown of employer contributions
    """
    salary = Decimal(str(base_salary))

    # Employer contributions (approximate rates)
    # These can vary by industry and company agreements
    employer_pension = salary * Decimal("0.001")  # SIS (employer pension): ~0.1%
    employer_health = Decimal("0")  # No employer health contribution in Chile
    employer_unemployment = salary * Decimal("0.024")  # Unemployment (employer): 2.4%
    employer_accident_insurance = salary * Decimal("0.0094")  # Mutual de Seguridad: ~0.94%

    total_employer = (
        employer_pension +
        employer_health +
        employer_unemployment +
        employer_accident_insurance
    )

    total_cost = salary + total_employer

    return {
        "employee_salary": float(salary.quantize(Decimal("0.01"))),
        "employer_contributions": {
            "pension_sis": float(employer_pension.quantize(Decimal("0.01"))),
            "health": float(employer_health.quantize(Decimal("0.01"))),
            "unemployment": float(employer_unemployment.quantize(Decimal("0.01"))),
            "accident_insurance": float(employer_accident_insurance.quantize(Decimal("0.01"))),
            "total": float(total_employer.quantize(Decimal("0.01"))),
        },
        "total_employment_cost": float(total_cost.quantize(Decimal("0.01"))),
    }
