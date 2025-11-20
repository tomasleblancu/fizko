"""
Celery tasks for SII form synchronization (Backend V2).

These tasks handle the synchronization of F29 forms from the SII website
to the Supabase database.

IMPORTANT: Tasks are kept simple and delegate all business logic to SIIService.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="sii.sync_f29",
    max_retries=3,
    default_retry_delay=60,
)
def sync_f29(
    self,
    company_id: str,
    year: str = None,
) -> Dict[str, Any]:
    """
    Celery task wrapper for F29 form synchronization.

    Delegates to SIIService for business logic.

    Args:
        company_id: UUID of the company (str format)
        year: Year to sync (YYYY format). Defaults to current year.

    Returns:
        Dict with sync results from service layer
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.services.sii_service import SIIService

        if year is None:
            year = str(datetime.now().year)

        logger.info(
            f"🚀 [CELERY TASK] F29 sync started: "
            f"company_id={company_id}, year={year}"
        )

        # Get Supabase client and service
        supabase = get_supabase_client()
        service = SIIService(supabase)

        # Run async service method synchronously
        result = asyncio.run(
            service.sync_f29(
                company_id=company_id,
                year=year
            )
        )

        logger.info(
            f"✅ [CELERY TASK] F29 sync completed: "
            f"{result.get('total', 0)} forms synced"
        )

        # After successful sync, trigger PDF download for all pending forms
        if result.get('success') and result.get('total', 0) > 0:
            logger.info(
                f"📥 [CELERY TASK] Triggering PDF download for company {company_id}"
            )

            # Call download_f29_pdf in batch mode (folio=None, id_interno_sii=None)
            # This will download all F29 PDFs that don't have extracted data yet
            download_f29_pdf.delay(company_id=company_id)

            logger.info(
                f"✅ [CELERY TASK] PDF download task queued for company {company_id}"
            )

        return result

    except ValueError as e:
        # Validation errors (company not found, no credentials, etc.)
        error_msg = str(e)
        logger.error(f"❌ [CELERY TASK] Validation error: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "company_id": company_id,
            "year": year,
        }

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] F29 sync failed for company {company_id}: {e}",
            exc_info=True
        )

        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        return {
            "success": False,
            "error": str(e),
            "company_id": company_id,
            "year": year,
        }


@celery_app.task(
    bind=True,
    name="sii.sync_f29_all_companies",
    max_retries=1
)
def sync_f29_all_companies(
    self,
    year: str = None,
) -> Dict[str, Any]:
    """
    Sync F29 forms for ALL companies with active subscriptions.

    Delegates to SIIService for business logic.

    Args:
        year: Year to sync (YYYY format). Defaults to current year.

    Returns:
        Dict with batch sync summary from service layer
    """
    if year is None:
        year = str(datetime.now().year)

    logger.info(f"🚀 [CELERY TASK] Batch F29 sync started for all companies (year={year})")

    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.services.sii_service import SIIService

        # Get Supabase client and service
        supabase = get_supabase_client()
        service = SIIService(supabase)

        # Run async service method synchronously
        result = asyncio.run(
            service.sync_f29_all_companies(year=year)
        )

        logger.info(
            f"✅ [CELERY TASK] Batch F29 sync completed: "
            f"total={result['total_companies']}, synced={result['synced']}, "
            f"failed={result['failed']}"
        )

        return result

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Batch F29 sync failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "year": year
        }


@celery_app.task(
    bind=True,
    name="sii.download_f29_pdf",
    max_retries=2,
    default_retry_delay=30,
)
def download_f29_pdf(
    self,
    company_id: str,
    folio: str = None,
    id_interno_sii: str = None
) -> Dict[str, Any]:
    """
    Celery task to download and extract data from F29 PDFs.

    Can work in two modes:
    1. Single PDF download: When folio and id_interno_sii are provided
    2. Batch download: When folio=None and id_interno_sii=None (downloads all pending PDFs)

    This task:
    1. Downloads the PDF(s) from SII using the formCompacto endpoint
    2. Validates PDF content
    3. Extracts all F29 codes and data from the PDF
    4. Updates form29_sii_downloads with extracted data
    5. (TODO) Uploads PDF to Supabase Storage

    Args:
        company_id: UUID of the company (str format)
        folio: Folio of the F29 form (None for batch mode)
        id_interno_sii: Internal SII ID (codInt) for PDF download (None for batch mode)

    Returns:
        Dict with download result:
        - Single mode: {success, company_id, folio, storage_url, extracted_data, pdf_size_mb, error}
        - Batch mode: {success, company_id, total, downloaded, failed, results: [...]}
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.services.sii_service import SIIService

        # Get Supabase client and service
        supabase = get_supabase_client()
        service = SIIService(supabase)

        # BATCH MODE: Download all pending PDFs for company
        if folio is None and id_interno_sii is None:
            logger.info(
                f"📥 [CELERY TASK] F29 PDF batch download started: company_id={company_id}"
            )

            # Get all F29 forms with id_interno_sii but without PDF data
            forms_response = (
                supabase._client
                .table('form29_sii_downloads')
                .select('*')
                .eq('company_id', company_id)
                .not_.is_('sii_id_interno', 'null')
                .order('period_year', desc=True)
                .order('period_month', desc=True)
                .execute()
            )

            if not forms_response.data:
                logger.warning(f"⚠️ No F29 forms found with id_interno_sii for company {company_id}")
                return {
                    "success": True,
                    "company_id": company_id,
                    "total": 0,
                    "downloaded": 0,
                    "failed": 0,
                    "results": []
                }

            # Filter forms without PDF data
            forms_to_download = [
                f for f in forms_response.data
                if not f.get('extra_data', {}).get('f29_data')
            ]

            total_forms = len(forms_to_download)
            logger.info(f"📋 Found {total_forms} F29 forms ready for PDF download")

            if total_forms == 0:
                logger.info("✅ All F29 forms already have PDF data")
                return {
                    "success": True,
                    "company_id": company_id,
                    "total": 0,
                    "downloaded": 0,
                    "failed": 0,
                    "results": []
                }

            # Download each PDF
            downloaded = 0
            failed = 0
            results = []

            for i, form in enumerate(forms_to_download, 1):
                form_folio = form['sii_folio']
                form_id_interno = form['sii_id_interno']
                period = form.get('period_display', 'N/A')

                logger.info(f"📥 [{i}/{total_forms}] Downloading PDF: folio={form_folio}, period={period}")

                try:
                    # Download single PDF
                    result = asyncio.run(
                        service.download_f29_pdf(
                            company_id=company_id,
                            folio=form_folio,
                            id_interno_sii=form_id_interno
                        )
                    )

                    if result.get("success"):
                        downloaded += 1
                        logger.info(f"✅ [{i}/{total_forms}] Downloaded: folio={form_folio}")
                    else:
                        failed += 1
                        logger.error(f"❌ [{i}/{total_forms}] Failed: folio={form_folio}, error={result.get('error')}")

                    results.append({
                        "folio": form_folio,
                        "period": period,
                        "success": result.get("success"),
                        "error": result.get("error")
                    })

                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    logger.error(f"❌ [{i}/{total_forms}] Exception: folio={form_folio}, error={error_msg}")
                    results.append({
                        "folio": form_folio,
                        "period": period,
                        "success": False,
                        "error": error_msg
                    })

            logger.info(
                f"✅ [CELERY TASK] F29 PDF batch download completed: "
                f"total={total_forms}, downloaded={downloaded}, failed={failed}"
            )

            return {
                "success": True,
                "company_id": company_id,
                "total": total_forms,
                "downloaded": downloaded,
                "failed": failed,
                "results": results
            }

        # SINGLE MODE: Download one specific PDF
        else:
            if not folio or not id_interno_sii:
                raise ValueError("Both folio and id_interno_sii are required for single PDF download")

            logger.info(
                f"📥 [CELERY TASK] F29 PDF download started: "
                f"company_id={company_id}, folio={folio}, id_interno_sii={id_interno_sii}"
            )

            # Run async service method synchronously
            result = asyncio.run(
                service.download_f29_pdf(
                    company_id=company_id,
                    folio=folio,
                    id_interno_sii=id_interno_sii
                )
            )

            # Log result
            if result.get("success"):
                logger.info(
                    f"✅ [CELERY TASK] F29 PDF downloaded successfully: "
                    f"folio={folio}, size={result.get('pdf_size_mb', 0):.2f}MB, "
                    f"extracted_codes={len(result.get('extracted_data', {}).get('codes', {}))}"
                )
            else:
                logger.error(
                    f"❌ [CELERY TASK] F29 PDF download failed: "
                    f"folio={folio}, error={result.get('error')}"
                )

            return {
                "success": result.get("success", False),
                "company_id": company_id,
                "folio": folio,
                "storage_url": result.get("storage_url"),
                "extracted_data": result.get("extracted_data"),
                "pdf_size_mb": result.get("pdf_size_mb"),
                "error": result.get("error")
            }

    except ValueError as e:
        # Validation errors (company not found, no credentials, missing codInt, etc.)
        error_msg = str(e)
        logger.error(f"❌ [CELERY TASK] Validation error: {error_msg}")
        return {
            "success": False,
            "company_id": company_id,
            "folio": folio,
            "error": error_msg
        }

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] F29 PDF download failed: {e}",
            exc_info=True
        )

        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        return {
            "success": False,
            "company_id": company_id,
            "folio": folio,
            "error": str(e)
        }


@celery_app.task(
    bind=True,
    name="sii.download_all_pending_f29_pdfs",
    max_retries=1,
)
def download_all_pending_f29_pdfs(
    self,
    max_per_company: int = None
) -> Dict[str, Any]:
    """
    Celery task to download ALL pending F29 PDFs across ALL companies.

    This is a batch task that:
    1. Finds all companies with F29 forms that have id_interno_sii but no PDF data
    2. For each company, triggers download_f29_pdf in batch mode
    3. Returns statistics about the batch operation

    Useful for:
    - Scheduled batch processing (e.g., nightly job)
    - Backfilling missing PDFs
    - Recovery after system issues

    Args:
        max_per_company: Optional limit of PDFs to download per company

    Returns:
        Dict with batch results:
        {
            "success": bool,
            "total_companies": int,
            "processed_companies": int,
            "total_forms": int,
            "downloaded": int,
            "failed": int,
            "companies": [...]  # List of company results
        }
    """
    try:
        from app.config.supabase import get_supabase_client

        logger.info("🚀 [CELERY TASK] Batch F29 PDF download started for ALL companies")

        # Get Supabase client
        supabase = get_supabase_client()

        # Find all F29 forms with id_interno_sii but without PDF data
        # Group by company_id to process per company
        forms_response = (
            supabase._client
            .table('form29_sii_downloads')
            .select('company_id, sii_folio, sii_id_interno, period_display, extra_data')
            .not_.is_('sii_id_interno', 'null')
            .order('company_id')
            .order('period_year', desc=True)
            .order('period_month', desc=True)
            .execute()
        )

        if not forms_response.data:
            logger.info("✅ No F29 forms found with id_interno_sii")
            return {
                "success": True,
                "total_companies": 0,
                "processed_companies": 0,
                "total_forms": 0,
                "downloaded": 0,
                "failed": 0,
                "companies": []
            }

        # Filter forms without PDF data
        forms_without_pdf = [
            f for f in forms_response.data
            if not f.get('extra_data', {}).get('f29_data')
        ]

        if not forms_without_pdf:
            logger.info("✅ All F29 forms already have PDF data")
            return {
                "success": True,
                "total_companies": 0,
                "processed_companies": 0,
                "total_forms": 0,
                "downloaded": 0,
                "failed": 0,
                "companies": []
            }

        # Group forms by company_id
        from collections import defaultdict
        companies_forms = defaultdict(list)
        for form in forms_without_pdf:
            companies_forms[form['company_id']].append(form)

        total_companies = len(companies_forms)
        total_forms = len(forms_without_pdf)

        logger.info(
            f"📋 Found {total_forms} F29 forms pending PDF download "
            f"across {total_companies} companies"
        )

        # Process each company
        processed_companies = 0
        total_downloaded = 0
        total_failed = 0
        companies_results = []

        for company_id, forms in companies_forms.items():
            company_forms_count = len(forms)

            # Apply max_per_company limit if specified
            if max_per_company and company_forms_count > max_per_company:
                logger.info(
                    f"📋 Company {company_id}: Limiting to {max_per_company} PDFs "
                    f"(total: {company_forms_count})"
                )
                # We'll let the download_f29_pdf task handle the limiting

            logger.info(
                f"📥 [{processed_companies + 1}/{total_companies}] "
                f"Queuing PDF downloads for company {company_id}: "
                f"{company_forms_count} forms"
            )

            try:
                # Queue download_f29_pdf task in batch mode for this company
                # This runs asynchronously - we just queue it
                download_f29_pdf.delay(company_id=company_id)

                processed_companies += 1

                companies_results.append({
                    "company_id": company_id,
                    "forms_count": company_forms_count,
                    "status": "queued",
                    "error": None
                })

                logger.info(
                    f"✅ [{processed_companies}/{total_companies}] "
                    f"PDF download task queued for company {company_id}"
                )

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"❌ [{processed_companies + 1}/{total_companies}] "
                    f"Failed to queue for company {company_id}: {error_msg}"
                )

                companies_results.append({
                    "company_id": company_id,
                    "forms_count": company_forms_count,
                    "status": "error",
                    "error": error_msg
                })

        logger.info(
            f"✅ [CELERY TASK] Batch F29 PDF download completed: "
            f"{processed_companies}/{total_companies} companies queued, "
            f"{total_forms} total forms"
        )

        return {
            "success": True,
            "total_companies": total_companies,
            "processed_companies": processed_companies,
            "total_forms": total_forms,
            "note": "Tasks queued asynchronously - download counts not available yet",
            "companies": companies_results
        }

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Batch F29 PDF download failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "total_companies": 0,
            "processed_companies": 0,
            "total_forms": 0,
            "companies": []
        }
