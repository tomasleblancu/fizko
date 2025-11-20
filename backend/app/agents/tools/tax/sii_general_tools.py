"""Tools for SII General Agent - Chilean tax authority (SII) regulations."""

from __future__ import annotations

import logging
from typing import Any

from agents import RunContextWrapper, function_tool

from app.agents.core import FizkoContext
from app.agents.tools.utils import get_supabase

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
    # Get company_id from context
    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    try:
        supabase = get_supabase()

        # Get company info (includes tax info via join)
        company = await supabase.companies.get_by_id(company_id)

        if not company:
            return {"error": "Empresa no encontrada"}

        # Build complete company info
        company_data = {
            "id": company.get("id"),
            "rut": company.get("rut"),
            "business_name": company.get("business_name"),
            "trade_name": company.get("trade_name"),
            "address": company.get("address"),
            "phone": company.get("phone"),
            "email": company.get("email"),
            "created_at": company.get("created_at"),
            "updated_at": company.get("updated_at"),
        }

        # Add tax info if available (from company_tax_info relation)
        tax_info = company.get("company_tax_info")
        if tax_info:
            company_data["tax_info"] = {
                "tax_regime": tax_info.get("tax_regime"),
                "sii_activity_code": tax_info.get("sii_activity_code"),
                "sii_activity_name": tax_info.get("sii_activity_name"),
                "legal_representative_rut": tax_info.get("legal_representative_rut"),
                "legal_representative_name": tax_info.get("legal_representative_name"),
                "start_of_activities_date": tax_info.get("start_of_activities_date"),
                "accounting_start_month": tax_info.get("accounting_start_month"),
            }

        return {"company": company_data}
    except Exception as e:
        logger.error(f"Error getting company info: {e}")
        return {"error": str(e)}


