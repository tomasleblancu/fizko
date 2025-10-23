"""Operación Renta Agent - Expert in Chilean annual tax declaration (Formulario 22)."""

from __future__ import annotations

import logging
from typing import Any
from datetime import date
from uuid import UUID

from agents import Agent, RunContextWrapper, function_tool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ...config.constants import MODEL, OPERACION_RENTA_INSTRUCTIONS
from ...config.database import AsyncSessionLocal
from ..context import FizkoContext
from ..tools.operacion_renta_tools import (
    calculate_annual_income_tax,
    explain_operacion_renta,
    calculate_global_complementario,
)

logger = logging.getLogger(__name__)


def create_operacion_renta_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Operación Renta Agent.

    This agent helps with:
    - Understanding annual tax declaration (Form 22)
    - Calculating annual income tax
    - Explaining tax credits and deductions
    - Preparing documentation for Operación Renta
    - Understanding different tax regimes' annual obligations
    """

    @function_tool(strict_mode=False)
    async def get_annual_summary(
        ctx: RunContextWrapper[FizkoContext],
        year: int,
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Get annual summary of documents and F29 for Operación Renta preparation.

        Args:
            year: Tax year
            company_id: Company UUID (optional, uses context if not provided)

        Returns:
            Annual summary with purchases, sales, IVA, and PPM totals
        """
        from ...db.models import PurchaseDocument, SalesDocument, Form29

        user_id = ctx.context.request_context.get("user_id")
        if not user_id:
            return {"error": "Usuario no autenticado"}

        # Get company_id from context if not provided
        if not company_id:
            company_id = ctx.context.request_context.get("company_id")
            if not company_id:
                return {"error": "company_id no disponible en el contexto"}

        try:
            async with AsyncSessionLocal() as session:
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)

                # Get all purchase documents for the year
                purchase_stmt = select(PurchaseDocument).where(
                    and_(
                        PurchaseDocument.company_id == UUID(company_id),
                        PurchaseDocument.issue_date >= start_date,
                        PurchaseDocument.issue_date <= end_date,
                    )
                )
                purchase_result = await session.execute(purchase_stmt)
                purchases = purchase_result.scalars().all()

                # Get all sales documents for the year
                sales_stmt = select(SalesDocument).where(
                    and_(
                        SalesDocument.company_id == UUID(company_id),
                        SalesDocument.issue_date >= start_date,
                        SalesDocument.issue_date <= end_date,
                    )
                )
                sales_result = await session.execute(sales_stmt)
                sales = sales_result.scalars().all()

                # Get all F29 records for the year
                form29_stmt = select(Form29).where(
                    and_(
                        Form29.company_id == UUID(company_id),
                        Form29.period_year == year,
                    )
                )
                form29_result = await session.execute(form29_stmt)
                form29_records = form29_result.scalars().all()

                # Calculate totals
                purchase_total = sum(float(doc.total_amount) for doc in purchases)
                purchase_iva = sum(float(doc.tax_amount) for doc in purchases)
                sales_total = sum(float(doc.total_amount) for doc in sales)
                sales_iva = sum(float(doc.tax_amount) for doc in sales)

                # Calculate annual IVA and PPM from F29
                annual_iva_paid = sum(
                    float(f29.iva_to_pay or 0) for f29 in form29_records
                )
                annual_ppm_paid = sum(
                    float(f29.ppm_amount or 0) for f29 in form29_records if f29.ppm_amount
                )

                return {
                    "year": year,
                    "company_id": company_id,
                    "purchases": {
                        "count": len(purchases),
                        "total_amount": purchase_total,
                        "total_iva": purchase_iva,
                    },
                    "sales": {
                        "count": len(sales),
                        "total_amount": sales_total,
                        "total_iva": sales_iva,
                    },
                    "annual_totals": {
                        "gross_income": sales_total,
                        "expenses": purchase_total,
                        "iva_paid_to_sii": annual_iva_paid,
                        "ppm_paid": annual_ppm_paid,
                    },
                    "f29_records": {
                        "count": len(form29_records),
                        "months_declared": [f29.period_month for f29 in form29_records],
                    },
                    "operacion_renta_notes": {
                        "gross_income_for_f22": sales_total,
                        "ppm_credit_available": annual_ppm_paid,
                        "recommendation": "Verifica estos montos con tu balance contable antes de declarar el F22",
                    },
                }

        except Exception as e:
            logger.error(f"Error getting annual summary: {e}")
            return {"error": str(e)}

    agent = Agent(
        name="operacion_renta_agent",
        model=MODEL,
        instructions=OPERACION_RENTA_INSTRUCTIONS,
        tools=[
            calculate_annual_income_tax,
            explain_operacion_renta,
            get_annual_summary,
            calculate_global_complementario,
        ],
    )

    return agent
