"""Tools for SII General Agent - Chilean tax authority (SII) regulations."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from agents import RunContextWrapper, function_tool
from sqlalchemy import select

from ....config.database import AsyncSessionLocal
from ...core import FizkoContext

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
async def get_company_info(
    ctx: RunContextWrapper[FizkoContext],
) -> dict[str, Any]:
    """
    Get information about the current company from context.

    Returns:
        Complete company information including basic data and tax info
    """
    from ....db.models import Company, CompanyTaxInfo

    # Get company_id from context
    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    try:
        async with AsyncSessionLocal() as db:
            # Get company basic info
            stmt = select(Company).where(Company.id == UUID(company_id))
            result = await db.execute(stmt)
            company = result.scalar_one_or_none()

            if not company:
                return {"error": "Empresa no encontrada"}

            # Get tax info
            tax_stmt = select(CompanyTaxInfo).where(CompanyTaxInfo.company_id == UUID(company_id))
            tax_result = await db.execute(tax_stmt)
            tax_info = tax_result.scalar_one_or_none()

            # Build complete company info
            company_data = {
                "id": str(company.id),
                "rut": company.rut,
                "business_name": company.business_name,
                "trade_name": company.trade_name,
                "address": company.address,
                "phone": company.phone,
                "email": company.email,
                "created_at": company.created_at.isoformat() if company.created_at else None,
                "updated_at": company.updated_at.isoformat() if company.updated_at else None,
            }

            # Add tax info if available
            if tax_info:
                company_data["tax_info"] = {
                    "tax_regime": tax_info.tax_regime,
                    "sii_activity_code": tax_info.sii_activity_code,
                    "sii_activity_name": tax_info.sii_activity_name,
                    "legal_representative_rut": tax_info.legal_representative_rut,
                    "legal_representative_name": tax_info.legal_representative_name,
                    "start_of_activities_date": tax_info.start_of_activities_date.isoformat() if tax_info.start_of_activities_date else None,
                    "accounting_start_month": tax_info.accounting_start_month,
                }

            return {"company": company_data}
    except Exception as e:
        logger.error(f"Error getting company info: {e}")
        return {"error": str(e)}


