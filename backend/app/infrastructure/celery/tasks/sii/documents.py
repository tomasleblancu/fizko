"""
Celery tasks for SII document synchronization (Backend V2).

These tasks handle the synchronization of tax documents (purchases and sales)
from the SII website to the Supabase database.

IMPORTANT: Tasks are kept simple and delegate all business logic to SIIService.
"""
import logging
from typing import Dict, Any

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="sii.sync_documents",
    max_retries=3,
    default_retry_delay=60,
)
def sync_documents(
    self,
    company_id: str,
    months: int = 1,
    month_offset: int = 0,
) -> Dict[str, Any]:
    """
    Celery task wrapper for tax documents sync (purchases and sales).

    Delegates to SIIService for business logic.

    Args:
        company_id: UUID of the company (str format)
        months: Number of months to sync (1-12)
        month_offset: Number of months to skip from current month
                     (0=current month, 1=last month, etc.)

    Returns:
        Dict with sync results from service layer
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.services.sii_service import SIIService

        logger.info(
            f"🚀 [CELERY TASK] Document sync started: "
            f"company_id={company_id}, months={months}, offset={month_offset}"
        )

        # Get Supabase client and service
        supabase = get_supabase_client()
        service = SIIService(supabase)

        # Run async service method synchronously
        # Celery tasks are synchronous, so we need to wrap async calls
        result = asyncio.run(
            service.sync_documents(
                company_id=company_id,
                months=months,
                month_offset=month_offset
            )
        )

        logger.info(
            f"✅ [CELERY TASK] Document sync completed: "
            f"compras={result['compras']}, ventas={result['ventas']}, "
            f"honorarios={result.get('honorarios', {'total': 0})}"
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
        }

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Document sync failed for company {company_id}: {e}",
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
        }


@celery_app.task(
    bind=True,
    name="sii.sync_documents_all_companies",
    max_retries=1
)
def sync_documents_all_companies(
    self,
    months: int = 1,
    month_offset: int = 0,
) -> Dict[str, Any]:
    """
    Sync documents for ALL companies with active subscriptions.

    Delegates to SIIService for business logic.

    Args:
        months: Number of months to sync per company
        month_offset: Month offset from current date

    Returns:
        Dict with batch sync summary from service layer
    """
    logger.info("🚀 [CELERY TASK] Batch document sync started for all companies")

    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.services.sii_service import SIIService

        # Get Supabase client and service
        supabase = get_supabase_client()
        service = SIIService(supabase)

        # Run async service method synchronously
        result = asyncio.run(
            service.sync_documents_all_companies(
                months=months,
                month_offset=month_offset
            )
        )

        logger.info(
            f"✅ [CELERY TASK] Batch document sync completed: "
            f"total={result['total_companies']}, synced={result['synced']}, "
            f"failed={result['failed']}"
        )

        return result

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Batch document sync failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e)
        }
