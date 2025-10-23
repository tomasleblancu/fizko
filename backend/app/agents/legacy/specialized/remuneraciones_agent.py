"""Remuneraciones Agent - Expert in Chilean payroll calculations."""

from __future__ import annotations

import logging

from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.constants import MODEL, REMUNERACIONES_INSTRUCTIONS
from ..tools.remuneraciones_tools import (
    calculate_salary,
    calculate_employer_contributions,
)

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
