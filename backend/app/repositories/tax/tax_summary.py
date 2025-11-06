"""Tax Summary Repository - Business logic for tax calculations and summaries."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import Company, PurchaseDocument, SalesDocument, Form29SIIDownload
from ...db.models.honorarios import HonorariosReceipt
from ...schemas.tax import TaxSummary


class TaxSummaryRepository:
    """
    Repository for tax summary calculations.

    Handles:
    - Tax summary calculations
    - IVA (sales tax) computations
    - Form 29 data extraction
    - Previous month credit lookups
    """

    def __init__(self, db: AsyncSession):
        """Initialize the tax summary repository with a database session."""
        self.db = db

    async def get_tax_summary(
        self,
        company_id: UUID,
        period: Optional[str] = None
    ) -> TaxSummary:
        """
        Calculate tax summary for a company in a given period.

        Args:
            company_id: Company UUID
            period: Period in format YYYY-MM (defaults to current month)

        Returns:
            TaxSummary with all calculated values

        Raises:
            ValueError: If company not found or invalid period format
        """
        # Verify company exists
        company = await self._get_company(company_id)
        if not company:
            raise ValueError("Company not found")

        # Parse period or use current month
        period_start, period_end = self._parse_period(period)

        # Calculate sales data
        total_revenue, iva_collected = await self._calculate_sales(
            company_id, period_start, period_end
        )

        # Calculate purchases data
        total_expenses, iva_paid = await self._calculate_purchases(
            company_id, period_start, period_end
        )

        # Calculate net IVA
        net_iva = iva_collected - iva_paid

        # Get previous month credit from F29
        previous_month_credit = await self._get_previous_month_credit(
            company_id, period_start
        )

        # Calculate PPM as 0.125% of total revenue
        ppm = self._calculate_ppm(total_revenue)

        # Get retención from honorarios receipts
        retencion = await self._get_retencion(
            company_id, period_start, period_end
        )

        # Get impuesto trabajadores (TODO: implement when payroll system exists)
        impuesto_trabajadores = None

        # Calculate monthly tax following Chilean tax formula:
        # 1. Calculate IVA balance (can be negative if credit > debit)
        iva_balance = iva_collected - iva_paid - (previous_month_credit or 0.0)

        # 2. IVA to pay (never negative - if negative, it's a credit for next month)
        iva_a_pagar = max(0.0, iva_balance)

        # 3. Add other monthly taxes (PPM, retención, impuesto trabajadores)
        monthly_tax = iva_a_pagar
        if ppm is not None and ppm > 0:
            monthly_tax += ppm
        if retencion is not None and retencion > 0:
            monthly_tax += retencion
        if impuesto_trabajadores is not None and impuesto_trabajadores > 0:
            monthly_tax += impuesto_trabajadores

        # TODO: Implement income tax calculation
        income_tax = 0.0

        # Generate summary ID
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
            ppm=ppm,
            retencion=retencion,
            impuesto_trabajadores=impuesto_trabajadores,
            monthly_tax=monthly_tax,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

    async def _get_company(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID."""
        stmt = select(Company).where(Company.id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _parse_period(self, period: Optional[str]) -> tuple[datetime, datetime]:
        """
        Parse period string or use current month.

        Args:
            period: Period string in format YYYY-MM or None

        Returns:
            Tuple of (period_start, period_end) datetimes

        Raises:
            ValueError: If period format is invalid
        """
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
                raise ValueError("Invalid period format. Use YYYY-MM")
        else:
            now = datetime.now()
            period_start = datetime(now.year, now.month, 1)
            if now.month == 12:
                period_end = datetime(now.year + 1, 1, 1)
            else:
                period_end = datetime(now.year, now.month + 1, 1)

        return period_start, period_end

    async def _calculate_sales(
        self,
        company_id: UUID,
        period_start: datetime,
        period_end: datetime
    ) -> tuple[float, float]:
        """
        Calculate total sales revenue and IVA collected.

        Formula:
        - Positive documents (facturas, boletas, notas de débito) ADD to totals
        - Credit notes (notas de crédito) SUBTRACT from totals

        Args:
            company_id: Company UUID
            period_start: Start of period
            period_end: End of period (exclusive)

        Returns:
            Tuple of (total_revenue, iva_collected)
        """
        # Positive documents (facturas, boletas, notas de débito)
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
        sales_positive_result = await self.db.execute(sales_positive_stmt)
        sales_positive_row = sales_positive_result.one()

        # Credit notes (subtract)
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
        sales_credit_result = await self.db.execute(sales_credit_stmt)
        sales_credit_row = sales_credit_result.one()

        # Calculate net sales
        total_revenue = float(sales_positive_row.total or 0) - float(sales_credit_row.total or 0)
        iva_collected = float(sales_positive_row.tax or 0) - float(sales_credit_row.tax or 0)

        return total_revenue, iva_collected

    async def _calculate_purchases(
        self,
        company_id: UUID,
        period_start: datetime,
        period_end: datetime
    ) -> tuple[float, float]:
        """
        Calculate total purchase expenses and IVA paid.

        Formula:
        - Positive documents (facturas, liquidaciones, notas de débito) ADD to totals
        - Credit notes (notas de crédito) SUBTRACT from totals

        Args:
            company_id: Company UUID
            period_start: Start of period
            period_end: End of period (exclusive)

        Returns:
            Tuple of (total_expenses, iva_paid)
        """
        # Positive documents (facturas, liquidaciones, notas de débito)
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
        purchases_positive_result = await self.db.execute(purchases_positive_stmt)
        purchases_positive_row = purchases_positive_result.one()

        # Credit notes (subtract)
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
        purchases_credit_result = await self.db.execute(purchases_credit_stmt)
        purchases_credit_row = purchases_credit_result.one()

        # Calculate net purchases
        total_expenses = float(purchases_positive_row.total or 0) - float(purchases_credit_row.total or 0)
        iva_paid = float(purchases_positive_row.tax or 0) - float(purchases_credit_row.tax or 0)

        return total_expenses, iva_paid

    async def _get_previous_month_credit(
        self,
        company_id: UUID,
        period_start: datetime
    ) -> Optional[float]:
        """
        Get credit from previous month's F29 (código 077).

        Looks for the "Vigente" (valid) F29 of the previous month
        and extracts code 077 (Remanente crédito fiscal mes anterior).

        Args:
            company_id: Company UUID
            period_start: Current period start date

        Returns:
            Previous month credit amount or None if not found
        """
        try:
            # Calculate previous month
            if period_start.month == 1:
                prev_year = period_start.year - 1
                prev_month = 12
            else:
                prev_year = period_start.year
                prev_month = period_start.month - 1

            # Query for the "Vigente" F29 of previous month
            f29_stmt = select(Form29SIIDownload).where(
                and_(
                    Form29SIIDownload.company_id == company_id,
                    Form29SIIDownload.period_year == prev_year,
                    Form29SIIDownload.period_month == prev_month,
                    Form29SIIDownload.status == 'Vigente'
                )
            ).order_by(Form29SIIDownload.created_at.desc()).limit(1)

            result = await self.db.execute(f29_stmt)
            f29 = result.scalar_one_or_none()

            if f29 and f29.extra_data:
                # Extract code 077 from extra_data
                f29_data = f29.extra_data.get("f29_data", {})
                codes = f29_data.get("codes", {})
                code_077 = codes.get("077", {})
                remanente_value = code_077.get("value")

                if remanente_value is not None:
                    return float(remanente_value)

        except Exception:
            # Return None on any error
            pass

        return None

    def _calculate_ppm(self, total_revenue: float) -> Optional[float]:
        """
        Calculate PPM (Pago Provisional Mensual) as 0.125% of total revenue.

        PPM is a monthly provisional payment towards annual income tax.
        It's calculated as 0.125% of the total sales revenue for the period.

        Args:
            total_revenue: Total sales revenue for the period

        Returns:
            PPM amount (0.125% of revenue) or None if revenue is 0
        """
        # Calculate PPM as 0.125% of total revenue
        if total_revenue > 0:
            return total_revenue * 0.00125  # 0.125%

        return None

    async def _get_retencion(
        self,
        company_id: UUID,
        period_start: datetime,
        period_end: datetime
    ) -> Optional[float]:
        """
        Get retención (withholding) from honorarios receipts.

        Retención is the tax withholding from professional services invoices
        (boletas de honorarios). Typically 12.25% in Chile.

        Args:
            company_id: Company UUID
            period_start: Period start date
            period_end: Period end date (exclusive)

        Returns:
            Total retención amount or None if no receipts found
        """
        try:
            # Sum recipient_retention from honorarios receipts received
            # (receipts where we pay and withhold tax)
            stmt = select(
                func.coalesce(func.sum(HonorariosReceipt.recipient_retention), 0).label("retencion")
            ).where(
                and_(
                    HonorariosReceipt.company_id == company_id,
                    HonorariosReceipt.issue_date >= period_start.date(),
                    HonorariosReceipt.issue_date < period_end.date(),
                    HonorariosReceipt.receipt_type == 'received'  # Only receipts we received (paid)
                )
            )

            result = await self.db.execute(stmt)
            row = result.one()
            retencion = float(row.retencion) if row.retencion else 0.0

            return retencion if retencion > 0 else None

        except Exception:
            # Return None on any error
            pass

        return None
