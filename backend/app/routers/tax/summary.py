"""Tax Summary router - Get company tax summaries."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import Company, PurchaseDocument, SalesDocument, Form29SIIDownload
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/tax-summary",
    tags=["tax-summary"],
    dependencies=[Depends(require_auth)]
)


class TaxSummary(BaseModel):
    """Tax summary response model"""
    id: str
    company_id: str
    period_start: str
    period_end: str
    total_revenue: float
    total_expenses: float
    iva_collected: float
    iva_paid: float
    net_iva: float
    income_tax: float
    previous_month_credit: Optional[float] = None
    monthly_tax: float
    created_at: str
    updated_at: str


@router.get("/{company_id}", response_model=TaxSummary)
async def get_tax_summary(
    company_id: UUID,
    period: Optional[str] = Query(None, description="Period in format YYYY-MM"),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tax summary for a company.

    Calculates summary from sales and purchase documents.
    If no period is specified, returns current month summary.
    """

    # Verify company exists
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Parse period or use current month
    if period:
        try:
            year, month = map(int, period.split('-'))
            period_start = datetime(year, month, 1)
            # Calculate last day of month
            if month == 12:
                period_end = datetime(year + 1, 1, 1)
            else:
                period_end = datetime(year, month + 1, 1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid period format. Use YYYY-MM"
            )
    else:
        now = datetime.now()
        period_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1)
        else:
            period_end = datetime(now.year, now.month + 1, 1)

    # Get sales documents for period
    # Facturas y boletas suman (+), notas de crédito restan (-), notas de débito suman (+)

    # Documentos positivos (facturas, boletas, notas de débito)
    sales_positive_stmt = select(
        func.sum(SalesDocument.total_amount).label('total'),
        func.sum(SalesDocument.tax_amount).label('tax')
    ).where(
        and_(
            SalesDocument.company_id == company_id,
            SalesDocument.issue_date >= period_start.date(),
            SalesDocument.issue_date < period_end.date(),
            SalesDocument.document_type.in_([
                'factura_venta', 'boleta', 'boleta_exenta',
                'factura_exenta', 'comprobante_pago',
                'liquidacion_factura', 'nota_debito_venta'
            ])
        )
    )
    sales_positive_result = await db.execute(sales_positive_stmt)
    sales_positive_row = sales_positive_result.one()

    # Notas de crédito (restan)
    sales_credit_stmt = select(
        func.sum(SalesDocument.total_amount).label('total'),
        func.sum(SalesDocument.tax_amount).label('tax')
    ).where(
        and_(
            SalesDocument.company_id == company_id,
            SalesDocument.issue_date >= period_start.date(),
            SalesDocument.issue_date < period_end.date(),
            SalesDocument.document_type == 'nota_credito_venta'
        )
    )
    sales_credit_result = await db.execute(sales_credit_stmt)
    sales_credit_row = sales_credit_result.one()

    # Calcular totales de ventas (positivos - créditos)
    total_revenue = float(sales_positive_row.total or 0) - float(sales_credit_row.total or 0)
    iva_collected = float(sales_positive_row.tax or 0) - float(sales_credit_row.tax or 0)

    # Get purchase documents for period
    # Facturas de compra suman (+), notas de crédito restan (-), notas de débito suman (+)

    # Documentos positivos (facturas, liquidaciones, notas de débito)
    purchases_positive_stmt = select(
        func.sum(PurchaseDocument.total_amount).label('total'),
        func.sum(PurchaseDocument.tax_amount).label('tax')
    ).where(
        and_(
            PurchaseDocument.company_id == company_id,
            PurchaseDocument.issue_date >= period_start.date(),
            PurchaseDocument.issue_date < period_end.date(),
            PurchaseDocument.document_type.in_([
                'factura_compra', 'factura_exenta_compra',
                'liquidacion_factura', 'nota_debito_compra'
            ])
        )
    )
    purchases_positive_result = await db.execute(purchases_positive_stmt)
    purchases_positive_row = purchases_positive_result.one()

    # Notas de crédito de compra (restan del gasto)
    purchases_credit_stmt = select(
        func.sum(PurchaseDocument.total_amount).label('total'),
        func.sum(PurchaseDocument.tax_amount).label('tax')
    ).where(
        and_(
            PurchaseDocument.company_id == company_id,
            PurchaseDocument.issue_date >= period_start.date(),
            PurchaseDocument.issue_date < period_end.date(),
            PurchaseDocument.document_type == 'nota_credito_compra'
        )
    )
    purchases_credit_result = await db.execute(purchases_credit_stmt)
    purchases_credit_row = purchases_credit_result.one()

    # Calcular totales de compras (positivos - créditos)
    total_expenses = float(purchases_positive_row.total or 0) - float(purchases_credit_row.total or 0)
    iva_paid = float(purchases_positive_row.tax or 0) - float(purchases_credit_row.tax or 0)

    # Calculate net IVA
    net_iva = iva_collected - iva_paid

    # Placeholder for income tax calculation
    # TODO: Implement proper income tax calculation based on tax regime
    income_tax = 0.0

    # Get previous month credit from F29 (código 077 - Remanente crédito fiscal mes anterior)
    previous_month_credit = None
    try:
        # Calculate previous month period
        if period_start.month == 1:
            prev_year = period_start.year - 1
            prev_month = 12
        else:
            prev_year = period_start.year
            prev_month = period_start.month - 1

        # Query for the "Vigente" (valid) F29 of previous month
        f29_prev_stmt = select(Form29SIIDownload).where(
            and_(
                Form29SIIDownload.company_id == company_id,
                Form29SIIDownload.period_year == prev_year,
                Form29SIIDownload.period_month == prev_month,
                Form29SIIDownload.status == 'Vigente'
            )
        ).order_by(Form29SIIDownload.created_at.desc()).limit(1)

        f29_prev_result = await db.execute(f29_prev_stmt)
        f29_prev = f29_prev_result.scalar_one_or_none()

        if f29_prev and f29_prev.extra_data:
            # Extract remanente from extra_data["f29_data"]["codes"]["077"]["value"]
            f29_data = f29_prev.extra_data.get("f29_data", {})
            codes = f29_data.get("codes", {})
            code_077 = codes.get("077", {})
            remanente_value = code_077.get("value")

            if remanente_value is not None:
                # Convert to float if it's a string or int
                previous_month_credit = float(remanente_value)
    except Exception as e:
        # Log error but don't fail the request
        # previous_month_credit remains None if there's any error
        pass

    # Calculate monthly tax: IVA cobrado - IVA pagado - crédito mes anterior
    # If previous_month_credit is None, treat it as 0
    # If the result is negative (credit in favor), show 0 as tax to pay
    monthly_tax = max(0.0, iva_collected - iva_paid - (previous_month_credit or 0.0))

    # Generate summary ID from company_id and period
    summary_id = f"{company_id}-{period_start.year}-{period_start.month:02d}"

    return TaxSummary(
        id=summary_id,
        company_id=str(company_id),
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        iva_collected=iva_collected,
        iva_paid=iva_paid,
        net_iva=net_iva,
        income_tax=income_tax,
        previous_month_credit=previous_month_credit,
        monthly_tax=monthly_tax,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
