"""
Form29 Service - Business logic for Form29 draft management.
"""
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Form29, Company
from app.repositories.tax.form29 import Form29Repository
from app.repositories.tax.tax_summary import TaxSummaryRepository

logger = logging.getLogger(__name__)


class Form29Service:
    """
    Service for Form29 management.

    Responsibilities:
    - Calculate F29 from tax documents (DTEs)
    - Create and manage draft forms
    - Validate forms before submission
    - Generate F29 for specific periods
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.form29_repo = Form29Repository(db)
        self.tax_summary_repo = TaxSummaryRepository(db)

    async def calculate_f29_from_documents(
        self,
        company_id: UUID,
        period_year: int,
        period_month: int
    ) -> Dict[str, Decimal]:
        """
        Calculate Form29 values from tax documents for a given period.

        Uses the same calculation logic as the tax-summary endpoint to ensure
        consistency across the platform.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)

        Returns:
            Dictionary with calculated values
        """
        # Format period as YYYY-MM for TaxSummaryRepository
        period = f"{period_year}-{period_month:02d}"

        try:
            # Use TaxSummaryRepository to get calculated values
            summary = await self.tax_summary_repo.get_tax_summary(
                company_id, period
            )

            # Map tax summary fields to Form29 fields
            total_revenue = Decimal(str(summary.total_revenue))
            total_expenses = Decimal(str(summary.total_expenses))
            iva_collected = Decimal(str(summary.iva_collected))
            iva_paid = Decimal(str(summary.iva_paid))
            previous_month_credit = Decimal(str(summary.previous_month_credit or 0))

            # For Form29, we separate taxable and exempt sales
            # Assuming all revenue is taxable unless tax is 0
            taxable_sales = total_revenue - iva_collected if iva_collected > 0 else Decimal("0")
            exempt_sales = total_revenue if iva_collected == 0 else Decimal("0")

            # Same for purchases
            taxable_purchases = total_expenses - iva_paid if iva_paid > 0 else Decimal("0")

            # Calculate net IVA including previous month credit
            net_iva = iva_collected - iva_paid - previous_month_credit

            logger.info(
                f"Calculated F29 for company {company_id}, period {period}: "
                f"Revenue={total_revenue:,.0f}, IVA collected={iva_collected:,.0f}, "
                f"IVA paid={iva_paid:,.0f}, Previous month credit={previous_month_credit:,.0f}, "
                f"Net IVA={net_iva:,.0f}"
            )

            return {
                "total_sales": total_revenue,
                "taxable_sales": taxable_sales,
                "exempt_sales": exempt_sales,
                "sales_tax": iva_collected,
                "total_purchases": total_expenses,
                "taxable_purchases": taxable_purchases,
                "purchases_tax": iva_paid,
                "iva_to_pay": iva_collected,
                "iva_credit": iva_paid,
                "net_iva": net_iva,
                "previous_month_credit": previous_month_credit
            }

        except Exception as e:
            logger.error(
                f"Error calculating F29 from documents for company {company_id}, "
                f"period {period}: {e}"
            )
            # Return zero values on error
            return {
                "total_sales": Decimal("0"),
                "taxable_sales": Decimal("0"),
                "exempt_sales": Decimal("0"),
                "sales_tax": Decimal("0"),
                "total_purchases": Decimal("0"),
                "taxable_purchases": Decimal("0"),
                "purchases_tax": Decimal("0"),
                "iva_to_pay": Decimal("0"),
                "iva_credit": Decimal("0"),
                "net_iva": Decimal("0"),
                "previous_month_credit": Decimal("0")
            }

    async def create_draft_for_period(
        self,
        company_id: UUID,
        period_year: int,
        period_month: int,
        created_by_user_id: Optional[UUID] = None,
        auto_calculate: bool = True
    ) -> Tuple[Form29, bool]:
        """
        Create a Form29 draft for a specific period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)
            created_by_user_id: Optional user ID who created the draft
            auto_calculate: Whether to calculate values from tax documents

        Returns:
            Tuple of (Form29 instance, is_new: bool)
        """
        # Check if draft already exists
        existing = await self.form29_repo.find_by_period(
            company_id, period_year, period_month
        )

        if existing and not existing.is_cancelled:
            logger.info(
                f"Form29 already exists for company {company_id} "
                f"period {period_year}-{period_month:02d}"
            )
            return existing, False

        # Calculate values if requested
        calculated_values = {}
        if auto_calculate:
            try:
                calculated_values = await self.calculate_f29_from_documents(
                    company_id, period_year, period_month
                )
                logger.info(
                    f"Calculated F29 values for {period_year}-{period_month:02d}: "
                    f"Net IVA = ${calculated_values['net_iva']:,.0f}, "
                    f"Previous month credit applied = ${calculated_values.get('previous_month_credit', 0):,.0f}"
                )
            except Exception as e:
                logger.error(f"Error calculating F29 values: {e}")
                # Continue with zero values

        # Create draft (previous_month_credit is now stored in the model)
        form29 = await self.form29_repo.create_draft(
            company_id=company_id,
            period_year=period_year,
            period_month=period_month,
            created_by_user_id=created_by_user_id,
            **calculated_values
        )

        await self.db.commit()

        logger.info(
            f"Created Form29 draft for company {company_id} "
            f"period {period_year}-{period_month:02d} "
            f"(revision {form29.revision_number})"
        )

        return form29, True

    async def validate_draft(
        self,
        form29_id: UUID
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate a Form29 draft.

        Args:
            form29_id: Form29 UUID

        Returns:
            Tuple of (is_valid, validation_errors)
        """
        form29 = await self.form29_repo.get(form29_id)
        if not form29:
            return False, [{"field": "form29_id", "message": "Form29 not found"}]

        errors = []

        # Validation rules
        # 1. Check if period is in the future
        today = date.today()
        if form29.period_year > today.year or (
            form29.period_year == today.year and form29.period_month > today.month
        ):
            errors.append({
                "field": "period",
                "message": "Cannot create F29 for future periods"
            })

        # 2. Check if values are negative (should not happen)
        if form29.total_sales < 0:
            errors.append({
                "field": "total_sales",
                "message": "Total sales cannot be negative"
            })

        if form29.total_purchases < 0:
            errors.append({
                "field": "total_purchases",
                "message": "Total purchases cannot be negative"
            })

        # 3. Check IVA calculations
        expected_iva_to_pay = form29.sales_tax
        if abs(form29.iva_to_pay - expected_iva_to_pay) > Decimal("1"):
            errors.append({
                "field": "iva_to_pay",
                "message": f"IVA to pay mismatch. Expected: {expected_iva_to_pay}, Got: {form29.iva_to_pay}"
            })

        expected_iva_credit = form29.purchases_tax
        if abs(form29.iva_credit - expected_iva_credit) > Decimal("1"):
            errors.append({
                "field": "iva_credit",
                "message": f"IVA credit mismatch. Expected: {expected_iva_credit}, Got: {form29.iva_credit}"
            })

        expected_net_iva = form29.iva_to_pay - form29.iva_credit
        if abs(form29.net_iva - expected_net_iva) > Decimal("1"):
            errors.append({
                "field": "net_iva",
                "message": f"Net IVA mismatch. Expected: {expected_net_iva}, Got: {form29.net_iva}"
            })

        # Update validation status
        is_valid = len(errors) == 0
        validation_status = "valid" if is_valid else "invalid"

        await self.form29_repo.update_validation(
            form29_id, validation_status, errors
        )
        await self.db.commit()

        return is_valid, errors

    async def confirm_draft(
        self,
        form29_id: UUID,
        confirmed_by_user_id: UUID,
        confirmation_notes: Optional[str] = None
    ) -> Form29:
        """
        Confirm a draft for submission.

        Args:
            form29_id: Form29 UUID
            confirmed_by_user_id: User ID who confirmed
            confirmation_notes: Optional notes

        Returns:
            Updated Form29
        """
        # Validate first
        is_valid, errors = await self.validate_draft(form29_id)
        if not is_valid:
            raise ValueError(f"Form29 has validation errors: {errors}")

        form29 = await self.form29_repo.confirm_draft(
            form29_id, confirmed_by_user_id, confirmation_notes
        )

        if not form29:
            raise ValueError(f"Form29 {form29_id} not found")

        await self.db.commit()

        logger.info(
            f"Confirmed Form29 {form29_id} for submission "
            f"by user {confirmed_by_user_id}"
        )

        return form29

    async def create_drafts_for_all_companies(
        self,
        period_year: int,
        period_month: int,
        auto_calculate: bool = True
    ) -> Dict[str, Any]:
        """
        Create Form29 drafts for all active companies for a specific period.

        Args:
            period_year: Year
            period_month: Month (1-12)
            auto_calculate: Whether to calculate values from tax documents

        Returns:
            Dictionary with summary statistics
        """
        # Get all companies with active subscriptions
        from app.infrastructure.celery.subscription_helper import get_subscribed_companies

        subscribed_companies = await get_subscribed_companies(self.db, only_active=False)

        # Fetch full Company objects for the subscribed companies
        company_ids = [company_id for company_id, _ in subscribed_companies]

        if not company_ids:
            logger.info("No companies with active subscriptions found")
            return {
                "period_year": period_year,
                "period_month": period_month,
                "total_companies": 0,
                "created": 0,
                "skipped": 0,
                "errors": 0,
                "error_details": []
            }

        query = select(Company).where(Company.id.in_(company_ids))
        result = await self.db.execute(query)
        companies = result.scalars().all()

        total = len(companies)
        created = 0
        skipped = 0
        errors = 0
        error_details = []

        logger.info(
            f"Creating F29 drafts for {total} companies "
            f"for period {period_year}-{period_month:02d}"
        )

        for company in companies:
            try:
                form29, is_new = await self.create_draft_for_period(
                    company_id=company.id,
                    period_year=period_year,
                    period_month=period_month,
                    created_by_user_id=None,  # System-generated
                    auto_calculate=auto_calculate
                )

                if is_new:
                    created += 1
                    logger.info(
                        f"✅ Created F29 for {company.business_name} "
                        f"(Net IVA: ${form29.net_iva:,.0f})"
                    )
                else:
                    skipped += 1
                    logger.info(f"⏭️  Skipped {company.business_name} (already exists)")

            except Exception as e:
                errors += 1
                error_msg = str(e)
                error_details.append({
                    "company_id": str(company.id),
                    "company_name": company.business_name,
                    "error": error_msg
                })
                logger.error(
                    f"❌ Error creating F29 for {company.business_name}: {error_msg}"
                )

        summary = {
            "period_year": period_year,
            "period_month": period_month,
            "total_companies": total,
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "error_details": error_details
        }

        logger.info(
            f"✅ F29 draft creation complete: "
            f"{created} created, {skipped} skipped, {errors} errors"
        )

        return summary
