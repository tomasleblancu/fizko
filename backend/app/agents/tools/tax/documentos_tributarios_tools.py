"""Tools for Documentos Tributarios Agent - Chilean tax documents (DTE) queries."""

from __future__ import annotations

import json
import logging
from typing import Any
from datetime import datetime, date
from uuid import UUID

from agents import RunContextWrapper, function_tool
from sqlalchemy import select, and_, desc

from ...config.database import AsyncSessionLocal
from ...core import FizkoContext

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
async def search_documents_by_rut(
    ctx: RunContextWrapper[FizkoContext],
    rut: str,
    company_id: str | None = None,
    document_category: str = "both",
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search documents by RUT (supplier or customer).

    Args:
        rut: RUT to search (format: 12345678-9)
        company_id: Company UUID (optional, uses context if not provided)
        document_category: "purchase" (from suppliers), "sales" (to customers), or "both"
        limit: Number of documents to return (default 20, max 50)

    Returns:
        Documents from/to the specified RUT
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
            results = {"purchase_documents": [], "sales_documents": []}

            if document_category in ["purchase", "both"]:
                purchase_stmt = select(PurchaseDocument).where(
                    and_(
                        PurchaseDocument.company_id == UUID(company_id),
                        PurchaseDocument.sender_rut == rut,
                    )
                ).order_by(desc(PurchaseDocument.issue_date)).limit(min(limit, 50))

                purchase_result = await session.execute(purchase_stmt)
                purchases = purchase_result.scalars().all()

                results["purchase_documents"] = [
                    {
                        "id": str(doc.id),
                        "document_type": doc.document_type,
                        "folio": doc.folio,
                        "issue_date": doc.issue_date.isoformat(),
                        "sender_name": doc.sender_name,
                        "total_amount": float(doc.total_amount),
                        "status": doc.status,
                    }
                    for doc in purchases
                ]

            if document_category in ["sales", "both"]:
                sales_stmt = select(SalesDocument).where(
                    and_(
                        SalesDocument.company_id == UUID(company_id),
                        SalesDocument.recipient_rut == rut,
                    )
                ).order_by(desc(SalesDocument.issue_date)).limit(min(limit, 50))

                sales_result = await session.execute(sales_stmt)
                sales = sales_result.scalars().all()

                results["sales_documents"] = [
                    {
                        "id": str(doc.id),
                        "document_type": doc.document_type,
                        "folio": doc.folio,
                        "issue_date": doc.issue_date.isoformat(),
                        "recipient_name": doc.recipient_name,
                        "total_amount": float(doc.total_amount),
                        "status": doc.status,
                    }
                    for doc in sales
                ]

            total_found = len(results["purchase_documents"]) + len(results["sales_documents"])

            return {
                "rut": rut,
                "total_found": total_found,
                "results": results
            }

    except Exception as e:
        logger.error(f"Error searching documents by RUT: {e}")
        return {"error": str(e)}


@function_tool(strict_mode=False)
async def search_document_by_folio(
    ctx: RunContextWrapper[FizkoContext],
    folio: int,
    company_id: str | None = None,
    document_category: str = "both",
) -> dict[str, Any]:
    """
    Search a specific document by its folio number.

    Args:
        folio: Folio number to search
        company_id: Company UUID (optional, uses context if not provided)
        document_category: "purchase", "sales", or "both"

    Returns:
        Document(s) with the specified folio
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
            results = {"purchase_documents": [], "sales_documents": []}

            if document_category in ["purchase", "both"]:
                purchase_stmt = select(PurchaseDocument).where(
                    and_(
                        PurchaseDocument.company_id == UUID(company_id),
                        PurchaseDocument.folio == folio,
                    )
                )
                purchase_result = await session.execute(purchase_stmt)
                purchases = purchase_result.scalars().all()

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

            if document_category in ["sales", "both"]:
                sales_stmt = select(SalesDocument).where(
                    and_(
                        SalesDocument.company_id == UUID(company_id),
                        SalesDocument.folio == folio,
                    )
                )
                sales_result = await session.execute(sales_stmt)
                sales = sales_result.scalars().all()

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

            total_found = len(results["purchase_documents"]) + len(results["sales_documents"])

            if total_found == 0:
                return {
                    "folio": folio,
                    "message": f"No se encontraron documentos con folio {folio}",
                    "results": results
                }

            return {
                "folio": folio,
                "total_found": total_found,
                "results": results
            }

    except Exception as e:
        logger.error(f"Error searching document by folio: {e}")
        return {"error": str(e)}


@function_tool(strict_mode=False)
async def get_documents_by_date_range(
    ctx: RunContextWrapper[FizkoContext],
    start_date: str,
    end_date: str,
    company_id: str | None = None,
    document_category: str = "both",
    limit: int = 50,
) -> dict[str, Any]:
    """
    Get documents within a specific date range.

    Args:
        start_date: Start date (format: YYYY-MM-DD)
        end_date: End date (format: YYYY-MM-DD)
        company_id: Company UUID (optional, uses context if not provided)
        document_category: "purchase", "sales", or "both"
        limit: Maximum documents per category (default 50, max 100)

    Returns:
        Documents within the date range
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
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        async with AsyncSessionLocal() as session:
            results = {"purchase_documents": [], "sales_documents": []}

            if document_category in ["purchase", "both"]:
                purchase_stmt = select(PurchaseDocument).where(
                    and_(
                        PurchaseDocument.company_id == UUID(company_id),
                        PurchaseDocument.issue_date >= start,
                        PurchaseDocument.issue_date <= end,
                    )
                ).order_by(desc(PurchaseDocument.issue_date)).limit(min(limit, 100))

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
                        "sender_name": doc.sender_name,
                        "total_amount": float(doc.total_amount),
                        "tax_amount": float(doc.tax_amount),
                    }
                    for doc in purchases
                ]

                results["purchase_summary"] = {
                    "count": len(purchases),
                    "total_amount": purchase_total,
                    "total_iva": purchase_iva,
                }

            if document_category in ["sales", "both"]:
                sales_stmt = select(SalesDocument).where(
                    and_(
                        SalesDocument.company_id == UUID(company_id),
                        SalesDocument.issue_date >= start,
                        SalesDocument.issue_date <= end,
                    )
                ).order_by(desc(SalesDocument.issue_date)).limit(min(limit, 100))

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
                        "recipient_name": doc.recipient_name,
                        "total_amount": float(doc.total_amount),
                        "tax_amount": float(doc.tax_amount),
                    }
                    for doc in sales
                ]

                results["sales_summary"] = {
                    "count": len(sales),
                    "total_amount": sales_total,
                    "total_iva": sales_iva,
                }

            return {
                "date_range": {
                    "start": start_date,
                    "end": end_date,
                },
                "results": results
            }

    except ValueError as e:
        return {"error": f"Formato de fecha inválido. Use YYYY-MM-DD. Error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error getting documents by date range: {e}")
        return {"error": str(e)}


@function_tool(strict_mode=False)
async def get_purchase_documents(
    ctx: RunContextWrapper[FizkoContext],
    company_id: str | None = None,
    limit: int = 10,
    document_type: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """
    Get purchase documents (documentos de compra - facturas recibidas).

    Args:
        company_id: Company UUID (optional, uses context if not provided)
        limit: Number of documents to return (default 10, max 50)
        document_type: Filter by document type (factura_compra, factura_exenta_compra, nota_credito_compra, nota_debito_compra, liquidacion_factura)
        status: Filter by status (pending, approved, rejected, cancelled)

    Returns:
        List of purchase documents with details
    """
    from ...db.models import PurchaseDocument

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
            # Build query
            stmt = select(PurchaseDocument).where(
                PurchaseDocument.company_id == UUID(company_id)
            )

            if document_type:
                stmt = stmt.where(PurchaseDocument.document_type == document_type)
            if status:
                stmt = stmt.where(PurchaseDocument.status == status)

            stmt = stmt.order_by(desc(PurchaseDocument.issue_date)).limit(min(limit, 50))

            result = await session.execute(stmt)
            documents = result.scalars().all()

            return {
                "total": len(documents),
                "documents": [
                    {
                        "id": str(doc.id),
                        "document_type": doc.document_type,
                        "folio": doc.folio,
                        "issue_date": doc.issue_date.isoformat(),
                        "sender_rut": doc.sender_rut,
                        "sender_name": doc.sender_name,
                        "net_amount": float(doc.net_amount),
                        "tax_amount": float(doc.tax_amount),
                        "exempt_amount": float(doc.exempt_amount),
                        "total_amount": float(doc.total_amount),
                        "status": doc.status,
                    }
                    for doc in documents
                ]
            }

    except Exception as e:
        logger.error(f"Error getting purchase documents: {e}")
        return {"error": str(e)}


@function_tool(strict_mode=False)
async def get_sales_documents(
    ctx: RunContextWrapper[FizkoContext],
    company_id: str | None = None,
    limit: int = 10,
    document_type: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """
    Get sales documents (documentos de venta - facturas emitidas).

    Args:
        company_id: Company UUID (optional, uses context if not provided)
        limit: Number of documents to return (default 10, max 50)
        document_type: Filter by document type (factura_venta, boleta, factura_exenta, nota_credito_venta, nota_debito_venta, liquidacion_factura)
        status: Filter by status (pending, approved, rejected, cancelled)

    Returns:
        List of sales documents with details
    """
    from ...db.models import SalesDocument

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
            # Build query
            stmt = select(SalesDocument).where(
                SalesDocument.company_id == UUID(company_id)
            )

            if document_type:
                stmt = stmt.where(SalesDocument.document_type == document_type)
            if status:
                stmt = stmt.where(SalesDocument.status == status)

            stmt = stmt.order_by(desc(SalesDocument.issue_date)).limit(min(limit, 50))

            result = await session.execute(stmt)
            documents = result.scalars().all()

            return {
                "total": len(documents),
                "documents": [
                    {
                        "id": str(doc.id),
                        "document_type": doc.document_type,
                        "folio": doc.folio,
                        "issue_date": doc.issue_date.isoformat(),
                        "recipient_rut": doc.recipient_rut,
                        "recipient_name": doc.recipient_name,
                        "net_amount": float(doc.net_amount),
                        "tax_amount": float(doc.tax_amount),
                        "exempt_amount": float(doc.exempt_amount),
                        "total_amount": float(doc.total_amount),
                        "status": doc.status,
                    }
                    for doc in documents
                ]
            }

    except Exception as e:
        logger.error(f"Error getting sales documents: {e}")
        return {"error": str(e)}


@function_tool(strict_mode=False)
async def get_document_details(
    ctx: RunContextWrapper[FizkoContext],
    document_id: str,
    document_category: str,
) -> dict[str, Any]:
    """
    Get detailed information about a specific document.

    Args:
        document_id: Document UUID
        document_category: Category of document ("purchase" or "sales")

    Returns:
        Detailed document information
    """
    from ...db.models import PurchaseDocument, SalesDocument

    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    try:
        async with AsyncSessionLocal() as session:
            if document_category == "purchase":
                stmt = select(PurchaseDocument).where(PurchaseDocument.id == UUID(document_id))
                result = await session.execute(stmt)
                doc = result.scalar_one_or_none()

                if not doc:
                    return {"error": "Documento no encontrado"}

                return {
                    "id": str(doc.id),
                    "company_id": str(doc.company_id),
                    "document_type": doc.document_type,
                    "folio": doc.folio,
                    "issue_date": doc.issue_date.isoformat(),
                    "sender_rut": doc.sender_rut,
                    "sender_name": doc.sender_name,
                    "net_amount": float(doc.net_amount),
                    "tax_amount": float(doc.tax_amount),
                    "exempt_amount": float(doc.exempt_amount),
                    "total_amount": float(doc.total_amount),
                    "status": doc.status,
                    "sii_track_id": doc.sii_track_id,
                    "created_at": doc.created_at.isoformat(),
                }

            elif document_category == "sales":
                stmt = select(SalesDocument).where(SalesDocument.id == UUID(document_id))
                result = await session.execute(stmt)
                doc = result.scalar_one_or_none()

                if not doc:
                    return {"error": "Documento no encontrado"}

                return {
                    "id": str(doc.id),
                    "company_id": str(doc.company_id),
                    "document_type": doc.document_type,
                    "folio": doc.folio,
                    "issue_date": doc.issue_date.isoformat(),
                    "recipient_rut": doc.recipient_rut,
                    "recipient_name": doc.recipient_name,
                    "net_amount": float(doc.net_amount),
                    "tax_amount": float(doc.tax_amount),
                    "exempt_amount": float(doc.exempt_amount),
                    "total_amount": float(doc.total_amount),
                    "status": doc.status,
                    "sii_track_id": doc.sii_track_id,
                    "created_at": doc.created_at.isoformat(),
                }

            else:
                return {"error": "Categoría de documento inválida. Usa 'purchase' o 'sales'"}

    except Exception as e:
        logger.error(f"Error getting document details: {e}")
        return {"error": str(e)}


@function_tool(strict_mode=False)
async def get_documents_summary(
    ctx: RunContextWrapper[FizkoContext],
    month: int | None = None,
    year: int | None = None,
) -> dict[str, Any]:
    """
    Get a summary of purchase and sales documents for a period.

    Args:
        month: Month (1-12), optional. If not provided, uses current month.
        year: Year, optional. If not provided, uses current year.

    Returns:
        Summary with totals and counts by document type including IVA calculations
    """
    import time
    from ...db.models import PurchaseDocument, SalesDocument

    tool_start = time.time()
    logger.info("=" * 60)
    logger.info(f"🔧 [TOOL START] get_documents_summary(month={month}, year={year})")

    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        logger.error("❌ Usuario no autenticado")
        return {"error": "Usuario no autenticado"}

    # Always get company_id from context (never from agent parameter)
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
            sales_total = sum(float(doc.total_amount) for doc in sales)
            sales_iva = sum(float(doc.tax_amount) for doc in sales)

            logger.info(f"📊 Resumen calculado: {len(purchases)} compras (${purchase_total:,.0f}), {len(sales)} ventas (${sales_total:,.0f})")

            result = {
                "period": f"{year}-{month:02d}",
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
                "iva_summary": {
                    "debito_fiscal": sales_iva,  # IVA cobrado en ventas
                    "credito_fiscal": purchase_iva,  # IVA pagado en compras
                    "iva_a_pagar": sales_iva - purchase_iva,  # IVA neto a pagar (o saldo a favor)
                }
            }

            total_time = time.time() - tool_start
            logger.info(f"✅ [TOOL END] get_documents_summary completed: {total_time:.3f}s")
            logger.info("=" * 60)
            return result

    except Exception as e:
        logger.error(f"❌ Error getting documents summary: {e}", exc_info=True)
        return {"error": str(e)}
