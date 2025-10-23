"""F29 Agent - Expert in Chilean Form 29 (monthly tax declaration)."""

from __future__ import annotations

import logging
from typing import Any
from decimal import Decimal
from datetime import date
from uuid import UUID

from agents import Agent, RunContextWrapper, function_tool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ...config.constants import MODEL, F29_INSTRUCTIONS
from ...config.database import AsyncSessionLocal
from ..context import FizkoContext
from ..tools.f29_tools import (
    calculate_ppm,
    explain_f29_completion,
    calculate_f29_summary,
)

logger = logging.getLogger(__name__)


def create_f29_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the F29 Agent.

    This agent helps with:
    - Understanding Form 29 (monthly tax declaration)
    - Calculating IVA (debito fiscal - credito fiscal)
    - Calculating PPM (provisional monthly payment)
    - Explaining employee tax withholdings
    - Step-by-step F29 completion guide
    """

    @function_tool(strict_mode=False)
    async def calculate_f29_iva(
        ctx: RunContextWrapper[FizkoContext],
        month: int,
        year: int,
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate IVA (Value Added Tax) for Form 29 based on company documents.

        Args:
            month: Month (1-12)
            year: Year
            company_id: Company UUID (optional, uses context if not provided)

        Returns:
            IVA calculation breakdown (debito fiscal, credito fiscal, IVA to pay)
        """
        from ...db.models import PurchaseDocument, SalesDocument

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
                # Date range for the month
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1)
                else:
                    end_date = date(year, month + 1, 1)

                # Get sales documents (Debito Fiscal)
                sales_stmt = select(SalesDocument).where(
                    and_(
                        SalesDocument.company_id == UUID(company_id),
                        SalesDocument.issue_date >= start_date,
                        SalesDocument.issue_date < end_date,
                    )
                )
                sales_result = await session.execute(sales_stmt)
                sales_docs = sales_result.scalars().all()

                # Get purchase documents (Credito Fiscal)
                purchase_stmt = select(PurchaseDocument).where(
                    and_(
                        PurchaseDocument.company_id == UUID(company_id),
                        PurchaseDocument.issue_date >= start_date,
                        PurchaseDocument.issue_date < end_date,
                    )
                )
                purchase_result = await session.execute(purchase_stmt)
                purchase_docs = purchase_result.scalars().all()

                # Calculate debito fiscal (IVA charged on sales)
                debito_fiscal = sum(float(doc.tax_amount) for doc in sales_docs)

                # Calculate credito fiscal (IVA paid on purchases)
                credito_fiscal = sum(float(doc.tax_amount) for doc in purchase_docs)

                # Calculate IVA to pay (or refund)
                iva_determinado = debito_fiscal - credito_fiscal

                return {
                    "period": f"{year}-{month:02d}",
                    "libro_ventas": {
                        "total_documents": len(sales_docs),
                        "total_net": float(sum(doc.net_amount for doc in sales_docs)),
                        "debito_fiscal_iva": debito_fiscal,
                    },
                    "libro_compras": {
                        "total_documents": len(purchase_docs),
                        "total_net": float(sum(doc.net_amount for doc in purchase_docs)),
                        "credito_fiscal_iva": credito_fiscal,
                    },
                    "iva_calculation": {
                        "debito_fiscal": debito_fiscal,
                        "credito_fiscal": credito_fiscal,
                        "iva_determinado": iva_determinado,
                        "status": "A PAGAR" if iva_determinado > 0 else "SALDO A FAVOR",
                    },
                    "f29_line": "Línea 30 del F29: IVA Determinado",
                    "deadline": f"{year}-{month + 1 if month < 12 else 1:02d}-12 (día 12 del mes siguiente)",
                }

        except Exception as e:
            logger.error(f"Error calculating F29 IVA: {e}")
            return {"error": str(e)}

    agent = Agent(
        name="f29_agent",
        model=MODEL,
        instructions=F29_INSTRUCTIONS,
        tools=[
            calculate_f29_iva,
            calculate_ppm,
            explain_f29_completion,
            calculate_f29_summary,
        ],
    )

    return agent
