"""
Shared context loading for agents across all channels (Web, WhatsApp, etc.)
Ensures consistent company and user information formatting.
"""
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import Company, CompanyTaxInfo

logger = logging.getLogger(__name__)

# In-memory cache for company info (30 minute TTL)
_company_info_cache: Dict[str, tuple[datetime, Dict[str, Any]]] = {}
_CACHE_TTL_SECONDS = 1800  # 30 minutes (company info rarely changes)


async def load_company_info(
    db: AsyncSession,
    company_id: UUID | str,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Load complete company information including tax info.

    This is the canonical method for loading company context,
    used by both ChatKit (web) and WhatsApp channels.

    Args:
        db: Database session
        company_id: Company UUID
        use_cache: Whether to use in-memory cache (default: True)

    Returns:
        Dict with company data or error
    """
    import time
    load_start = time.time()

    try:
        company_uuid = UUID(company_id) if isinstance(company_id, str) else company_id
        cache_key = str(company_uuid)

        # Check cache first
        if use_cache and cache_key in _company_info_cache:
            cached_time, cached_data = _company_info_cache[cache_key]
            cache_age = (datetime.now() - cached_time).total_seconds()

            if cache_age < _CACHE_TTL_SECONDS:
                logger.debug(f"  💾 Cache HIT: {cache_age:.1f}s old ({(time.time() - load_start):.3f}s)")
                return cached_data
            else:
                logger.debug(f"  💾 Cache EXPIRED: {cache_age:.1f}s old")
                del _company_info_cache[cache_key]

        logger.debug(f"  💾 Cache MISS - fetching from DB")

        # Get company basic info
        company_query_start = time.time()
        stmt = select(Company).where(Company.id == company_uuid)
        result = await db.execute(stmt)
        company = result.scalar_one_or_none()
        logger.debug(f"  🔍 Company query: {(time.time() - company_query_start):.3f}s")

        if not company:
            logger.warning(f"⚠️ Company not found: {company_id}")
            return {"error": "Empresa no encontrada"}

        # Get tax info
        tax_query_start = time.time()
        tax_stmt = select(CompanyTaxInfo).where(
            CompanyTaxInfo.company_id == company_uuid
        )
        tax_result = await db.execute(tax_stmt)
        tax_info = tax_result.scalar_one_or_none()
        logger.debug(f"  🔍 Tax info query: {(time.time() - tax_query_start):.3f}s")

        # Build complete company info
        build_start = time.time()
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

        logger.debug(f"  📦 Data building: {(time.time() - build_start):.3f}s")

        result_data = {"company": company_data}

        # Store in cache
        if use_cache:
            _company_info_cache[cache_key] = (datetime.now(), result_data)
            logger.debug(f"  💾 Cached for {_CACHE_TTL_SECONDS}s")

        logger.debug(f"  ✅ Total load_company_info: {(time.time() - load_start):.3f}s")

        return result_data

    except Exception as e:
        logger.error(f"Error loading company info: {e}", exc_info=True)
        return {"error": str(e)}


def format_company_context(company_info: Dict[str, Any]) -> str:
    """
    Format company information as XML context for the agent.

    This ensures consistent formatting across all channels.
    Includes current date for temporal context.

    Args:
        company_info: Company data from load_company_info()

    Returns:
        Formatted XML string with company context
    """
    if "error" in company_info:
        return f"<company_info>Error: {company_info['error']}</company_info>\n\n"

    if "company" not in company_info:
        return "<company_info>No company data available</company_info>\n\n"

    company_data = company_info["company"]

    # Get current date in Chilean timezone (America/Santiago)
    from zoneinfo import ZoneInfo
    chile_tz = ZoneInfo("America/Santiago")
    current_date = datetime.now(chile_tz)

    # Format date in Spanish (e.g., "Lunes 29 de Octubre de 2025")
    months_es = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    days_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    day_name = days_es[current_date.weekday()]
    month_name = months_es[current_date.month - 1]
    formatted_date = f"{day_name} {current_date.day} de {month_name} de {current_date.year}"

    # Build company context with current date at the top
    context = f"""<company_info>
Fecha actual: {formatted_date}

RUT: {company_data.get('rut', 'N/A')}
Razón Social: {company_data.get('business_name', 'N/A')}
Nombre Fantasía: {company_data.get('trade_name', 'N/A')}"""

    # Add tax info if available
    if "tax_info" in company_data:
        tax_info = company_data["tax_info"]
        context += f"""
Régimen Tributario: {tax_info.get('tax_regime', 'N/A')}
Código Actividad: {tax_info.get('sii_activity_code', 'N/A')} - {tax_info.get('sii_activity_name', 'N/A')}
Representante Legal: {tax_info.get('legal_representative_name', 'N/A')} (RUT: {tax_info.get('legal_representative_rut', 'N/A')})"""

    context += "\n</company_info>\n\n"

    return context
