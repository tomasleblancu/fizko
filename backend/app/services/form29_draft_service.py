"""
Form29 Draft Service - Business logic for Form29 draft generation and management.

This service handles the automatic generation and calculation of Form29 drafts
from tax documents, providing the foundation for monthly IVA declarations.
"""

import logging
from datetime import datetime, date
from typing import Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class Form29DraftService:
    """
    Service for Form29 draft management.

    Responsibilities:
    - Generate F29 drafts from tax documents using TaxSummaryService
    - Create and update draft forms
    - Batch processing for multiple companies
    - Validate draft data
    """

    def __init__(self, supabase_client):
        """
        Initialize service with Supabase client.

        Args:
            supabase_client: SupabaseClient instance with repository access
        """
        self.supabase = supabase_client
        from app.repositories.f29 import F29Repository
        from app.services.tax_summary_service import TaxSummaryService

        self.f29_repo = F29Repository(supabase_client.client)
        self.tax_summary_service = TaxSummaryService(supabase_client)

    async def calculate_f29_from_documents(
        self,
        company_id: str,
        period_year: int,
        period_month: int
    ) -> dict[str, Any]:
        """
        Calculate Form29 values from tax documents for a given period.

        Uses TaxSummaryService to get IVA calculations with proper credit note
        handling and previous month credit.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)

        Returns:
            Dictionary with calculated Form29 values
        """
        period = f"{period_year}-{period_month:02d}"

        try:
            # Get IVA summary from tax documents
            iva_summary = await self.tax_summary_service.get_iva_summary(
                company_id, period
            )

            # Get revenue and expense summaries
            revenue_summary = await self.tax_summary_service.get_revenue_summary(
                company_id, period
            )

            expense_summary = await self.tax_summary_service.get_expense_summary(
                company_id, period
            )

            # Map to Form29 fields - IVA components
            debito_fiscal = float(iva_summary.get("debito_fiscal", 0))
            credito_fiscal = float(iva_summary.get("credito_fiscal", 0))
            previous_month_credit = float(iva_summary.get("previous_month_credit", 0))
            overdue_iva_credit = float(iva_summary.get("overdue_iva_credit", 0))

            # Additional tax components (from iva_summary)
            ppm = float(iva_summary.get("ppm", 0))
            retencion = float(iva_summary.get("retencion", 0))
            reverse_charge_withholding = float(iva_summary.get("reverse_charge_withholding", 0))

            total_revenue = float(revenue_summary.get("total_revenue", 0))
            net_revenue = float(revenue_summary.get("net_revenue", 0))

            total_expenses = float(expense_summary.get("total_expenses", 0))
            net_expenses = float(expense_summary.get("net_expenses", 0))

            # For Form29, we separate taxable and exempt sales/purchases
            # Taxable sales = net revenue (revenue without IVA)
            # Total sales = total revenue (includes IVA)
            taxable_sales = net_revenue
            total_sales = total_revenue
            exempt_sales = 0  # We don't have this split yet from tax_summary_service

            # Purchases
            taxable_purchases = net_expenses
            total_purchases = total_expenses

            # Calculate net IVA including previous month credit and overdue
            # net_iva = debito - credito - previous_credit + overdue
            net_iva = debito_fiscal - credito_fiscal - previous_month_credit + overdue_iva_credit

            logger.info(
                f"Calculated F29 for company {company_id}, period {period}: "
                f"Débito={debito_fiscal:,.0f}, Crédito={credito_fiscal:,.0f}, "
                f"Previous credit={previous_month_credit:,.0f}, "
                f"Overdue={overdue_iva_credit:,.0f}, Net IVA={net_iva:,.0f}, "
                f"PPM={ppm:,.0f}, Retención={retencion:,.0f}, "
                f"Reverse Charge={reverse_charge_withholding:,.0f}"
            )

            return {
                # Sales data
                "total_sales": total_sales,
                "taxable_sales": taxable_sales,
                "exempt_sales": exempt_sales,
                "sales_tax": debito_fiscal,

                # Purchases data
                "total_purchases": total_purchases,
                "taxable_purchases": taxable_purchases,
                "purchases_tax": credito_fiscal,

                # IVA calculation
                "iva_to_pay": debito_fiscal,
                "iva_credit": credito_fiscal,
                "net_iva": net_iva,
                "previous_month_credit": previous_month_credit,
                "overdue_iva_credit": overdue_iva_credit,

                # Additional tax components
                "ppm": ppm,
                "retencion": retencion,
                "reverse_charge_withholding": reverse_charge_withholding,
                "impuesto_trabajadores": 0.0,  # TODO: Will be added when payroll is integrated
            }

        except Exception as e:
            logger.error(
                f"Error calculating F29 from documents for company {company_id}, "
                f"period {period}: {e}",
                exc_info=True
            )
            # Return zero values on error
            return {
                # Sales data
                "total_sales": 0,
                "taxable_sales": 0,
                "exempt_sales": 0,
                "sales_tax": 0,

                # Purchases data
                "total_purchases": 0,
                "taxable_purchases": 0,
                "purchases_tax": 0,

                # IVA calculation
                "iva_to_pay": 0,
                "iva_credit": 0,
                "net_iva": 0,
                "previous_month_credit": 0,
                "overdue_iva_credit": 0,

                # Additional tax components
                "ppm": 0,
                "retencion": 0,
                "reverse_charge_withholding": 0,
                "impuesto_trabajadores": 0,
            }

    async def create_draft_for_period(
        self,
        company_id: str,
        period_year: int,
        period_month: int,
        created_by_user_id: str | None = None,
        auto_calculate: bool = True,
        fetch_sii_proposal: bool = True
    ) -> tuple[dict[str, Any] | None, bool]:
        """
        Create a Form29 draft for a specific period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)
            created_by_user_id: Optional user ID who created the draft
            auto_calculate: Whether to calculate values from tax documents
            fetch_sii_proposal: Whether to fetch SII proposal after creating draft (default: True)

        Returns:
            Tuple of (Form29 draft dict, is_new: bool)
        """
        # Check if draft already exists
        existing = await self.f29_repo.get_draft_by_period(
            company_id, period_year, period_month
        )

        if existing and existing.get("status") != "cancelled":
            logger.info(
                f"Form29 draft already exists for company {company_id} "
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
                    f"Previous month credit = ${calculated_values.get('previous_month_credit', 0):,.0f}"
                )
            except Exception as e:
                logger.error(f"Error calculating F29 values: {e}", exc_info=True)
                # Continue with zero values

        # Create draft
        form29 = await self.f29_repo.create_draft(
            company_id=company_id,
            period_year=period_year,
            period_month=period_month,
            created_by_user_id=created_by_user_id,
            **calculated_values
        )

        if form29:
            logger.info(
                f"Created Form29 draft for company {company_id} "
                f"period {period_year}-{period_month:02d} "
                f"(revision {form29.get('revision_number')})"
            )

            # Fetch SII proposal if requested
            if fetch_sii_proposal:
                try:
                    # Get company credentials
                    company_response = (
                        self.supabase.client
                        .table("companies")
                        .select("rut, sii_password")
                        .eq("id", company_id)
                        .maybe_single()
                        .execute()
                    )

                    company_data = company_response.data if hasattr(company_response, 'data') else None

                    if company_data and company_data.get("rut") and company_data.get("sii_password"):
                        logger.info(
                            f"📊 Fetching SII proposal for Form29 draft {form29.get('id')}"
                        )

                        # Fetch and update SII proposal
                        updated_form29 = await self.fetch_and_update_sii_proposal(
                            form29_id=form29.get("id"),
                            company_rut=company_data["rut"],
                            company_sii_password=company_data["sii_password"]
                        )

                        if updated_form29:
                            form29 = updated_form29
                    else:
                        logger.warning(
                            f"⚠️ Cannot fetch SII proposal: Company {company_id} missing RUT or SII password"
                        )

                except Exception as e:
                    logger.error(
                        f"❌ Error fetching SII proposal for Form29 draft: {e}",
                        exc_info=True
                    )
                    # Continue without SII proposal - don't fail the draft creation

            return form29, True

        return None, False

    async def create_drafts_for_all_companies(
        self,
        period_year: int,
        period_month: int,
        auto_calculate: bool = True,
        fetch_sii_proposal: bool = True
    ) -> dict[str, Any]:
        """
        Create Form29 drafts for all active companies for a specific period.

        This is the main method used by Celery tasks for batch processing.

        Args:
            period_year: Year
            period_month: Month (1-12)
            auto_calculate: Whether to calculate values from tax documents
            fetch_sii_proposal: Whether to fetch SII proposal for each draft (default: True)

        Returns:
            Dictionary with summary statistics
        """
        # Get all companies with active subscriptions
        try:
            # Query companies with active subscriptions
            # NOTE: This uses the subscriptions system to only process active companies
            response = (
                self.supabase.client
                .table("subscriptions")
                .select("company_id, companies(id, business_name)")
                .eq("status", "active")
                .execute()
            )

            subscriptions = response.data if hasattr(response, 'data') else []
            companies = []

            for sub in subscriptions:
                company_data = sub.get("companies")
                if company_data:
                    companies.append({
                        "id": company_data.get("id"),
                        "business_name": company_data.get("business_name")
                    })

            if not companies:
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
                company_id = company["id"]
                company_name = company.get("business_name", "Unknown")

                try:
                    form29, is_new = await self.create_draft_for_period(
                        company_id=company_id,
                        period_year=period_year,
                        period_month=period_month,
                        created_by_user_id=None,  # System-generated
                        auto_calculate=auto_calculate,
                        fetch_sii_proposal=fetch_sii_proposal
                    )

                    if is_new:
                        created += 1
                        net_iva = form29.get("net_iva", 0) if form29 else 0
                        logger.info(
                            f"✅ Created F29 for {company_name} "
                            f"(Net IVA: ${net_iva:,.0f})"
                        )
                    else:
                        skipped += 1
                        logger.info(f"⏭️  Skipped {company_name} (already exists)")

                except Exception as e:
                    errors += 1
                    error_msg = str(e)
                    error_details.append({
                        "company_id": str(company_id),
                        "company_name": company_name,
                        "error": error_msg
                    })
                    logger.error(
                        f"❌ Error creating F29 for {company_name}: {error_msg}",
                        exc_info=True
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

        except Exception as e:
            logger.error(f"Error in create_drafts_for_all_companies: {e}", exc_info=True)
            return {
                "period_year": period_year,
                "period_month": period_month,
                "total_companies": 0,
                "created": 0,
                "skipped": 0,
                "errors": 1,
                "error_details": [{"error": str(e)}]
            }

    async def validate_draft(
        self,
        form29: dict[str, Any]
    ) -> tuple[bool, list[dict[str, Any]]]:
        """
        Validate a Form29 draft.

        Args:
            form29: Form29 draft dict

        Returns:
            Tuple of (is_valid, validation_errors)
        """
        errors = []

        # Get form values
        period_year = form29.get("period_year")
        period_month = form29.get("period_month")
        total_sales = float(form29.get("total_sales", 0))
        total_purchases = float(form29.get("total_purchases", 0))
        iva_to_pay = float(form29.get("iva_to_pay", 0))
        iva_credit = float(form29.get("iva_credit", 0))
        sales_tax = float(form29.get("sales_tax", 0))
        purchases_tax = float(form29.get("purchases_tax", 0))
        net_iva = float(form29.get("net_iva", 0))

        # Validation rules
        # 1. Check if period is in the future
        today = date.today()
        if period_year > today.year or (
            period_year == today.year and period_month > today.month
        ):
            errors.append({
                "field": "period",
                "message": "Cannot create F29 for future periods"
            })

        # 2. Check if values are negative (should not happen)
        if total_sales < 0:
            errors.append({
                "field": "total_sales",
                "message": "Total sales cannot be negative"
            })

        if total_purchases < 0:
            errors.append({
                "field": "total_purchases",
                "message": "Total purchases cannot be negative"
            })

        # 3. Check IVA calculations
        expected_iva_to_pay = sales_tax
        if abs(iva_to_pay - expected_iva_to_pay) > 1:
            errors.append({
                "field": "iva_to_pay",
                "message": f"IVA to pay mismatch. Expected: {expected_iva_to_pay:.0f}, Got: {iva_to_pay:.0f}"
            })

        expected_iva_credit = purchases_tax
        if abs(iva_credit - expected_iva_credit) > 1:
            errors.append({
                "field": "iva_credit",
                "message": f"IVA credit mismatch. Expected: {expected_iva_credit:.0f}, Got: {iva_credit:.0f}"
            })

        # Note: net_iva includes previous month credit, so we don't validate exact equality
        # Just check it's reasonable
        basic_net_iva = iva_to_pay - iva_credit
        if abs(net_iva - basic_net_iva) > float(form29.get("previous_month_credit", 0)) + 100:
            # Allow some tolerance for rounding and previous credit
            errors.append({
                "field": "net_iva",
                "message": f"Net IVA calculation appears incorrect. Basic: {basic_net_iva:.0f}, Final: {net_iva:.0f}"
            })

        is_valid = len(errors) == 0

        # Update validation status in database
        if form29.get("id"):
            validation_status = "valid" if is_valid else "invalid"
            await self.f29_repo.update_draft(
                form29["id"],
                validation_status=validation_status,
                validation_errors=errors
            )

        return is_valid, errors

    async def fetch_and_update_sii_proposal(
        self,
        form29_id: str,
        company_rut: str,
        company_sii_password: str
    ) -> Optional[dict[str, Any]]:
        """
        Fetch SII proposal for a Form29 draft and update the sii_proposal field.

        This method:
        1. Gets the Form29 draft from database
        2. Creates a SII client and logs in (synchronous operation)
        3. Fetches the SII proposal (pre-calculated values from SII)
        4. Updates the draft with the proposal

        Args:
            form29_id: Form29 UUID
            company_rut: Company RUT for SII authentication
            company_sii_password: Company SII password (will be decrypted if encrypted)

        Returns:
            Updated Form29 draft with sii_proposal, or None on error

        Example:
            >>> draft = await service.fetch_and_update_sii_proposal(
            ...     form29_id="uuid-here",
            ...     company_rut="12345678-9",
            ...     company_sii_password="secret"
            ... )
            >>> proposal = draft.get("sii_proposal")
            >>> codigos = proposal["data"]["listCodPropuestos"]
        """
        try:
            # Get the draft
            draft = await self.f29_repo.get_form_by_id(form29_id)
            if not draft:
                logger.error(f"Form29 draft not found: {form29_id}")
                return None

            period_year = draft.get("period_year")
            period_month = draft.get("period_month")
            periodo = f"{period_year}{period_month:02d}"

            logger.info(
                f"📊 Fetching SII proposal for Form29 {form29_id}, "
                f"period {period_year}-{period_month:02d}"
            )

            # Import dependencies
            from app.integrations.sii.client import SIIClient
            from app.utils.encryption import decrypt_password

            # Decrypt SII password (stored encrypted in database)
            try:
                decrypted_password = decrypt_password(company_sii_password)
            except Exception as e:
                logger.error(
                    f"❌ Failed to decrypt SII password for Form29 {form29_id}: {e}"
                )
                return None

            # Create SII client and get proposal
            # Note: SIIClient is synchronous, using context manager
            with SIIClient(
                tax_id=company_rut,
                password=decrypted_password
            ) as client:
                # Login to SII (synchronous)
                client.login()

                # Get the proposal (synchronous)
                proposal = client.get_propuesta_f29(periodo)

                if not proposal:
                    logger.warning(
                        f"No SII proposal available for period {periodo}"
                    )
                    return draft

                # Extract relevant info for logging
                codigos_propuestos = proposal.get("data", {}).get("listCodPropuestos", [])
                codigos_complementar = proposal.get("data", {}).get("listCodComplementar", [])

                logger.info(
                    f"✅ SII proposal retrieved: {len(codigos_propuestos)} códigos propuestos, "
                    f"{len(codigos_complementar)} códigos a complementar"
                )

            # Update the draft with the proposal (async)
            updated_draft = await self.f29_repo.update_draft(
                form29_id,
                sii_proposal=proposal
            )

            logger.info(
                f"✅ Updated Form29 {form29_id} with SII proposal"
            )

            return updated_draft

        except Exception as e:
            logger.error(
                f"❌ Error fetching SII proposal for Form29 {form29_id}: {e}",
                exc_info=True
            )
            return None
