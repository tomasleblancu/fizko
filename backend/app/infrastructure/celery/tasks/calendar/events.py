"""
Calendar Event Celery Tasks

Tasks for syncing calendar events from company_events.
"""
import logging
from typing import Dict, Any

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="calendar.sync_company_calendar",
    max_retries=2,
    default_retry_delay=60,
)
def sync_company_calendar(
    self,
    company_id: str
) -> Dict[str, Any]:
    """
    Celery task to synchronize calendar events for a specific company.

    This task:
    1. Auto-initializes company_events if none exist
       - Uses internal business logic to determine which templates to activate
       - Based on company settings (has_formal_employees, etc.)
    2. Gets active company_events for the company
    3. For each company_event, generates missing calendar_events
    4. Updates event statuses (first event -> in_progress, rest -> pending)
    5. Is idempotent - can be run multiple times without duplicating events

    Args:
        company_id: UUID of the company (str format)

    Returns:
        Dict with sync results:
        {
            "success": bool,
            "company_id": str,
            "company_name": str,
            "initialized": bool,  # True if company_events were created
            "company_events_created": int,  # Number of company_events created
            "active_company_events": list[str],  # event codes
            "created_events": list[str],  # labels
            "updated_events": list[str],
            "total_created": int,
            "total_updated": int,
            "message": str,
            "error": str  # only if failed
        }

    Example:
        >>> sync_company_calendar.delay("123e4567-e89b-12d3-a456-426614174000")
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.services.calendar_sync_service import CalendarSyncService

        logger.info(
            f"📅 [CELERY TASK] Calendar sync started: company_id={company_id}"
        )

        # Get Supabase client and service
        supabase = get_supabase_client()
        service = CalendarSyncService(supabase)

        # Run async service method synchronously
        result = asyncio.run(
            service.sync_company_calendar(company_id=company_id)
        )

        # Log result
        if result.get("success"):
            logger.info(
                f"✅ [CELERY TASK] Calendar sync completed: "
                f"company_id={company_id}, "
                f"created={result.get('total_created', 0)}, "
                f"updated={result.get('total_updated', 0)}"
            )
        else:
            logger.error(
                f"❌ [CELERY TASK] Calendar sync failed: "
                f"company_id={company_id}, "
                f"error={result.get('error')}"
            )

        return result

    except ValueError as e:
        # Validation errors (company not found, no active events, etc.)
        error_msg = str(e)
        logger.error(
            f"❌ [CELERY TASK] Validation error: {error_msg}"
        )
        return {
            "success": False,
            "company_id": company_id,
            "error": error_msg
        }

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Calendar sync failed: {e}",
            exc_info=True
        )

        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(
                f"🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        return {
            "success": False,
            "company_id": company_id,
            "error": str(e)
        }


@celery_app.task(
    bind=True,
    name="calendar.sync_all_calendars",
    max_retries=1,
)
def sync_all_calendars(self) -> Dict[str, Any]:
    """
    Celery task to synchronize calendar events for ALL companies with active events.

    This is a batch task that:
    1. Finds all companies with at least one active company_event
    2. For each company, syncs their calendar events
    3. Returns statistics about the batch operation

    Useful for:
    - Scheduled batch processing (e.g., nightly job)
    - Initial calendar population
    - Recovery after system issues

    Returns:
        Dict with batch sync results:
        {
            "success": bool,
            "total_companies": int,
            "synced_companies": int,
            "failed_companies": int,
            "results": list[dict]  # Per-company results
        }

    Example:
        >>> sync_all_calendars.delay()
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.services.calendar_sync_service import CalendarSyncService

        logger.info("🚀 [CELERY TASK] Batch calendar sync started for ALL companies")

        # Get Supabase client and service
        supabase = get_supabase_client()
        service = CalendarSyncService(supabase)

        # Run async service method synchronously
        result = asyncio.run(service.sync_all_companies())

        logger.info(
            f"✅ [CELERY TASK] Batch calendar sync completed: "
            f"{result.get('synced_companies', 0)}/{result.get('total_companies', 0)} companies synced, "
            f"{result.get('failed_companies', 0)} failed"
        )

        return result

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Batch calendar sync failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "total_companies": 0,
            "synced_companies": 0,
            "failed_companies": 0,
            "results": []
        }
