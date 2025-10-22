"""Remuneraciones Agent - Expert in Chilean payroll calculations."""

from __future__ import annotations

import logging
from typing import Any
from decimal import Decimal
from datetime import date

from agents import Agent, RunContextWrapper, function_tool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from ...config.constants import MODEL, REMUNERACIONES_INSTRUCTIONS
from ..context import FizkoContext

logger = logging.getLogger(__name__)


def create_remuneraciones_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Remuneraciones Agent.

    This agent helps with:
    - Salary calculations
    - Payroll tax calculations
    - Employee benefits and deductions
    - Payroll compliance
    """

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

    # TODO: Uncomment when PayrollRecord model is added to the database
    # @function_tool(strict_mode=False)
    # async def save_payroll_record(
    #     ctx: RunContextWrapper[FizkoContext],
    #     company_id: str,
    #     employee_rut: str,
    #     employee_name: str,
    #     base_salary: float,
    #     period_year: int,
    #     period_month: int,
    #     bonuses: float = 0,
    #     overtime: float = 0,
    # ) -> dict[str, Any]:
    #     """
    #     Save a payroll record to the database.
    #
    #     Args:
    #         company_id: Company UUID
    #         employee_rut: Employee RUT
    #         employee_name: Employee name
    #         base_salary: Base salary
    #         period_year: Year of payroll period
    #         period_month: Month of payroll period (1-12)
    #         bonuses: Bonuses
    #         overtime: Overtime pay
    #
    #     Returns:
    #         Created payroll record
    #     """
    #     from ...db.models import PayrollRecord
    #
    #     user_id = ctx.context.request_context.get("user_id")
    #     if not user_id:
    #         return {"error": "Usuario no autenticado"}
    #
    #     try:
    #         # Calculate salary components
    #         calculation = await calculate_salary(
    #             ctx,
    #             base_salary=base_salary,
    #             bonuses=bonuses,
    #             overtime=overtime,
    #         )
    #
    #         # Create payroll record
    #         payroll = PayrollRecord(
    #             company_id=UUID(company_id),
    #             user_id=UUID(user_id),
    #             employee_rut=employee_rut,
    #             employee_name=employee_name,
    #             period_year=period_year,
    #             period_month=period_month,
    #             base_salary=Decimal(str(base_salary)),
    #             bonuses=Decimal(str(bonuses)),
    #             overtime=Decimal(str(overtime)),
    #             gross_salary=Decimal(str(calculation["gross_salary"])),
    #             pension_contribution=Decimal(str(calculation["deductions"]["afp"])),
    #             health_contribution=Decimal(str(calculation["deductions"]["health"])),
    #             unemployment_insurance=Decimal(str(calculation["deductions"]["unemployment_insurance"])),
    #             income_tax=Decimal(str(calculation["deductions"]["income_tax"])),
    #             total_deductions=Decimal(str(calculation["deductions"]["total"])),
    #             net_salary=Decimal(str(calculation["net_salary"])),
    #             status="draft",
    #         )
    #
    #         db.add(payroll)
    #         await db.commit()
    #         await db.refresh(payroll)
    #
    #         return {
    #             "success": True,
    #             "payroll_id": str(payroll.id),
    #             "employee_name": employee_name,
    #             "net_salary": calculation["net_salary"],
    #             "period": f"{period_year}-{period_month:02d}",
    #         }
    #
    #     except Exception as e:
    #         logger.error(f"Error saving payroll record: {e}")
    #         await db.rollback()
    #         return {"error": str(e)}
    #
    # @function_tool(strict_mode=False)
    # async def get_payroll_records(
    #     ctx: RunContextWrapper[FizkoContext],
    #     company_id: str,
    #     period_year: int | None = None,
    #     period_month: int | None = None,
    # ) -> dict[str, Any]:
    #     """
    #     Get payroll records for a company.
    #
    #     Args:
    #         company_id: Company UUID
    #         period_year: Filter by year (optional)
    #         period_month: Filter by month (optional)
    #
    #     Returns:
    #         List of payroll records
    #     """
    #     from ...db.models import PayrollRecord
    #
    #     user_id = ctx.context.request_context.get("user_id")
    #     if not user_id:
    #         return {"error": "Usuario no autenticado"}
    #
    #     try:
    #         # Build query
    #         stmt = select(PayrollRecord).where(
    #             PayrollRecord.company_id == UUID(company_id),
    #             PayrollRecord.user_id == UUID(user_id),
    #         )
    #
    #         if period_year:
    #             stmt = stmt.where(PayrollRecord.period_year == period_year)
    #         if period_month:
    #             stmt = stmt.where(PayrollRecord.period_month == period_month)
    #
    #         stmt = stmt.order_by(
    #             PayrollRecord.period_year.desc(),
    #             PayrollRecord.period_month.desc()
    #         )
    #
    #         result = await db.execute(stmt)
    #         records = result.scalars().all()
    #
    #         return {
    #             "records": [
    #                 {
    #                     "id": str(r.id),
    #                     "employee_name": r.employee_name,
    #                     "employee_rut": r.employee_rut,
    #                     "period": f"{r.period_year}-{r.period_month:02d}",
    #                     "gross_salary": float(r.gross_salary),
    #                     "net_salary": float(r.net_salary),
    #                     "status": r.status,
    #                 }
    #                 for r in records
    #             ],
    #             "count": len(records),
    #         }
    #
    #     except Exception as e:
    #         logger.error(f"Error getting payroll records: {e}")
    #         return {"error": str(e)}

    agent = Agent(
        name="remuneraciones_agent",
        model=MODEL,
        instructions=REMUNERACIONES_INSTRUCTIONS,
        tools=[
            calculate_salary,
            calculate_employer_contributions,
            # TODO: Uncomment when PayrollRecord model is added
            # save_payroll_record,
            # get_payroll_records,
        ],
    )

    return agent
