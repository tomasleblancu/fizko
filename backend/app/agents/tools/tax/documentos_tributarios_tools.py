"""Tools for Documentos Tributarios Agent - Chilean tax documents (DTE) queries.

Simplified to 2 main tools:
1. get_documents() - Flexible search with multiple filters
2. get_documents_summary() - Monthly/yearly summaries with IVA calculations
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, date
from uuid import UUID

from agents import RunContextWrapper, function_tool
from sqlalchemy import select, and_, desc

from ....config.database import AsyncSessionLocal
from ...core import FizkoContext

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
async def get_documents(
    ctx: RunContextWrapper[FizkoContext],
    document_type: str = "both",
    rut: str | None = None,
    folio: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search and retrieve tax documents with flexible filters.

    This is the main tool for querying documents. All filters are optional and can be combined.

    Args:
        document_type: Type of documents to search:
            - "sales" = ventas (facturas emitidas, boletas)
            - "purchases" = compras (facturas recibidas)
            - "both" = ambos tipos (default)
        rut: Filter by RUT (supplier for purchases, customer for sales). Format: 12345678-9
        folio: Filter by folio number (exact match)
        start_date: Filter by start date (format: YYYY-MM-DD)
        end_date: Filter by end date (format: YYYY-MM-DD)
        limit: Maximum documents to return per type (default 20, max 100)

    Returns:
        Documents matching the filters with totals and summaries

    Examples:
        - Get last 10 sales: get_documents(document_type="sales", limit=10)
        - Search by RUT: get_documents(rut="12345678-9")
        - Search by folio: get_documents(folio=12345)
        - Date range: get_documents(start_date="2024-10-01", end_date="2024-10-31")
        - Combined: get_documents(document_type="purchases", rut="12345678-9", limit=5)
    """
    from ....db.models import PurchaseDocument, SalesDocument

    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    try:
        async with AsyncSessionLocal() as session:
            results = {
                "filters_applied": {
                    "document_type": document_type,
                    "rut": rut,
                    "folio": folio,
                    "date_range": f"{start_date} to {end_date}" if start_date and end_date else None,
                },
                "purchase_documents": [],
                "sales_documents": [],
            }

            # Parse dates if provided
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

            # Query purchases if needed
            if document_type in ["purchases", "both"]:
                purchase_conditions = [PurchaseDocument.company_id == UUID(company_id)]

                if rut:
                    purchase_conditions.append(PurchaseDocument.sender_rut == rut)
                if folio:
                    purchase_conditions.append(PurchaseDocument.folio == folio)
                if start_dt:
                    purchase_conditions.append(PurchaseDocument.issue_date >= start_dt)
                if end_dt:
                    purchase_conditions.append(PurchaseDocument.issue_date <= end_dt)

                purchase_stmt = (
                    select(PurchaseDocument)
                    .where(and_(*purchase_conditions))
                    .order_by(desc(PurchaseDocument.issue_date))
                    .limit(min(limit, 100))
                )

                purchase_result = await session.execute(purchase_stmt)
                purchases = purchase_result.scalars().all()

                purchase_total = sum(float(doc.total_amount) for doc in purchases)
                purchase_iva = sum(float(doc.tax_amount) for doc in purchases)

                results["purchase_documents"] = [
                    {
                        "id": str(doc.id),
                        "document_type": doc.document_type,
                        "folio": doc.folio,
                        "issue_date": doc.issue_date.isoformat(),
                        "sender_rut": doc.sender_rut,
                        "sender_name": doc.sender_name,
                        "net_amount": float(doc.net_amount),
                        "tax_amount": float(doc.tax_amount),
                        "total_amount": float(doc.total_amount),
                        "status": doc.status,
                    }
                    for doc in purchases
                ]

                results["purchase_summary"] = {
                    "count": len(purchases),
                    "total_amount": purchase_total,
                    "total_iva": purchase_iva,
                }

            # Query sales if needed
            if document_type in ["sales", "both"]:
                sales_conditions = [SalesDocument.company_id == UUID(company_id)]

                if rut:
                    sales_conditions.append(SalesDocument.recipient_rut == rut)
                if folio:
                    sales_conditions.append(SalesDocument.folio == folio)
                if start_dt:
                    sales_conditions.append(SalesDocument.issue_date >= start_dt)
                if end_dt:
                    sales_conditions.append(SalesDocument.issue_date <= end_dt)

                sales_stmt = (
                    select(SalesDocument)
                    .where(and_(*sales_conditions))
                    .order_by(desc(SalesDocument.issue_date))
                    .limit(min(limit, 100))
                )

                sales_result = await session.execute(sales_stmt)
                sales = sales_result.scalars().all()

                sales_total = sum(float(doc.total_amount) for doc in sales)
                sales_iva = sum(float(doc.tax_amount) for doc in sales)

                results["sales_documents"] = [
                    {
                        "id": str(doc.id),
                        "document_type": doc.document_type,
                        "folio": doc.folio,
                        "issue_date": doc.issue_date.isoformat(),
                        "recipient_rut": doc.recipient_rut,
                        "recipient_name": doc.recipient_name,
                        "net_amount": float(doc.net_amount),
                        "tax_amount": float(doc.tax_amount),
                        "total_amount": float(doc.total_amount),
                        "status": doc.status,
                    }
                    for doc in sales
                ]

                results["sales_summary"] = {
                    "count": len(sales),
                    "total_amount": sales_total,
                    "total_iva": sales_iva,
                }

            # Add total counts
            total_docs = len(results.get("purchase_documents", [])) + len(results.get("sales_documents", []))
            results["total_documents_found"] = total_docs

            if total_docs == 0:
                results["message"] = "No se encontraron documentos con los filtros aplicados"

            return results

    except ValueError as e:
        return {"error": f"Formato de fecha inválido. Use YYYY-MM-DD. Error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error in get_documents: {e}", exc_info=True)
        return {"error": str(e)}


@function_tool(strict_mode=False)
async def get_documents_summary(
    ctx: RunContextWrapper[FizkoContext],
    month: int | None = None,
    year: int | None = None,
) -> dict[str, Any]:
    """
    Get a summary of purchase and sales documents for a period.

    This tool provides aggregated totals and IVA calculations for a given month/year.
    Perfect for monthly reports, F29 declarations, and financial summaries.

    Args:
        month: Month (1-12). If not provided, uses current month.
        year: Year (e.g., 2024). If not provided, uses current year.

    Returns:
        Summary with:
        - Purchase totals (count, amounts, IVA)
        - Sales totals (count, amounts, IVA)
        - IVA summary (débito fiscal, crédito fiscal, IVA a pagar)

    Examples:
        - Current month summary: get_documents_summary()
        - Specific month: get_documents_summary(month=9, year=2024)
        - Last year summary: get_documents_summary(year=2023)
    """
    import time
    from ....db.models import PurchaseDocument, SalesDocument

    tool_start = time.time()
    logger.info("=" * 60)
    logger.info(f"🔧 [TOOL START] get_documents_summary(month={month}, year={year})")

    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        logger.error("❌ Usuario no autenticado")
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        logger.error("❌ company_id no disponible en el contexto")
        return {"error": "company_id no disponible en el contexto"}

    logger.info(f"✅ Contexto: user_id={user_id}, company_id={company_id}")

    try:
        db_start = time.time()
        async with AsyncSessionLocal() as session:
            logger.info(f"⏱️  DB session created: {time.time() - db_start:.3f}s")

            # Use current month/year if not provided
            if month is None or year is None:
                now = datetime.now()
                month = month or now.month
                year = year or now.year

            # Date range for the month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)

            # Purchase documents summary
            purchase_stmt = select(PurchaseDocument).where(
                and_(
                    PurchaseDocument.company_id == UUID(company_id),
                    PurchaseDocument.issue_date >= start_date,
                    PurchaseDocument.issue_date < end_date,
                )
            )
            purchase_result = await session.execute(purchase_stmt)
            purchases = purchase_result.scalars().all()

            # Sales documents summary
            sales_stmt = select(SalesDocument).where(
                and_(
                    SalesDocument.company_id == UUID(company_id),
                    SalesDocument.issue_date >= start_date,
                    SalesDocument.issue_date < end_date,
                )
            )
            sales_result = await session.execute(sales_stmt)
            sales = sales_result.scalars().all()

            # Calculate totals
            purchase_total = sum(float(doc.total_amount) for doc in purchases)
            purchase_iva = sum(float(doc.tax_amount) for doc in purchases)
            purchase_net = sum(float(doc.net_amount) for doc in purchases)

            sales_total = sum(float(doc.total_amount) for doc in sales)
            sales_iva = sum(float(doc.tax_amount) for doc in sales)
            sales_net = sum(float(doc.net_amount) for doc in sales)

            logger.info(
                f"📊 Resumen calculado: {len(purchases)} compras (${purchase_total:,.0f}), "
                f"{len(sales)} ventas (${sales_total:,.0f})"
            )

            result = {
                "period": {
                    "month": month,
                    "year": year,
                    "formatted": f"{year}-{month:02d}",
                },
                "purchases": {
                    "count": len(purchases),
                    "net_amount": purchase_net,
                    "tax_amount": purchase_iva,
                    "total_amount": purchase_total,
                },
                "sales": {
                    "count": len(sales),
                    "net_amount": sales_net,
                    "tax_amount": sales_iva,
                    "total_amount": sales_total,
                },
                "iva_summary": {
                    "debito_fiscal": sales_iva,  # IVA cobrado en ventas
                    "credito_fiscal": purchase_iva,  # IVA pagado en compras
                    "iva_a_pagar": sales_iva - purchase_iva,  # IVA neto a pagar (o saldo a favor)
                },
            }

            total_time = time.time() - tool_start
            logger.info(f"✅ [TOOL END] get_documents_summary completed: {total_time:.3f}s")
            logger.info("=" * 60)
            return result

    except Exception as e:
        logger.error(f"❌ Error getting documents summary: {e}", exc_info=True)
        return {"error": str(e)}
