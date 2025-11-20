"""Form29 draft generation Celery tasks."""

import logging
from typing import Any, Dict
from uuid import UUID

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="forms.generate_f29_drafts_all_companies",
    max_retries=2,
    default_retry_delay=300,
)
def generate_f29_drafts_all_companies(
    self,
    period_year: int = None,
    period_month: int = None,
    auto_calculate: bool = True
) -> Dict[str, Any]:
    """
    Generate Form29 drafts for all active companies for a specific period.

    This task creates F29 drafts with auto-calculated values from tax documents
    for all active companies in the system. Useful for monthly batch processing.

    Args:
        period_year: Year for the F29 period (defaults to current year)
        period_month: Month for the F29 period (1-12, defaults to previous month)
        auto_calculate: Whether to auto-calculate values from tax documents (default: True)

    Returns:
        Dict with summary:
        {
            "success": bool,
            "period_year": int,
            "period_month": int,
            "total_companies": int,
            "created": int,
            "skipped": int,
            "errors": int,
            "error_details": List[Dict],
            "execution_time_seconds": float
        }

    Example:
        # Generate drafts for January 2025
        generate_f29_drafts_all_companies.delay(period_year=2025, period_month=1)

        # Generate drafts for previous month (auto-detect)
        generate_f29_drafts_all_companies.delay()
    """
    import asyncio as async_lib
    from datetime import datetime
    from app.config.database import AsyncSessionLocal

    start_time = datetime.utcnow()

    try:
        # Default to previous month if not specified
        if period_year is None or period_month is None:
            now = datetime.utcnow()
            if period_month is None:
                period_month = now.month - 1 if now.month > 1 else 12
            if period_year is None:
                period_year = now.year if now.month > 1 else now.year - 1

        logger.info(
            f"📝 [CELERY TASK] Starting F29 draft generation for all companies: "
            f"period={period_year}-{period_month:02d}, auto_calculate={auto_calculate}"
        )

        async def _generate_drafts():
            """Async wrapper to call service"""
            from app.services.form29 import Form29Service

            async with AsyncSessionLocal() as db:
                service = Form29Service(db)
                summary = await service.create_drafts_for_all_companies(
                    period_year=period_year,
                    period_month=period_month,
                    auto_calculate=auto_calculate
                )
                # Note: service handles commits internally per company
                return summary

        # Run async function
        summary = async_lib.run(_generate_drafts())

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"✅ [CELERY TASK] F29 draft generation completed: "
            f"created={summary['created']}, skipped={summary['skipped']}, "
            f"errors={summary['errors']}, time={execution_time:.2f}s"
        )

        return {
            "success": True,
            "execution_time_seconds": execution_time,
            **summary
        }

    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"❌ [CELERY TASK] F29 draft generation failed: {e}",
            exc_info=True
        )

        # Retry on certain errors
        if "database" in str(e).lower() or "connection" in str(e).lower():
            raise self.retry(exc=e)

        return {
            "success": False,
            "error": str(e),
            "period_year": period_year,
            "period_month": period_month,
            "execution_time_seconds": execution_time,
            "total_companies": 0,
            "created": 0,
            "skipped": 0,
            "errors": 0,
            "error_details": []
        }


@celery_app.task(
    bind=True,
    name="forms.generate_f29_draft_for_company",
    max_retries=2,
    default_retry_delay=60,
)
def generate_f29_draft_for_company(
    self,
    company_id: str,
    period_year: int,
    period_month: int,
    auto_calculate: bool = True
) -> Dict[str, Any]:
    """
    Generate Form29 draft for a single company for a specific period.

    This task creates/updates a F29 draft with auto-calculated values from tax documents
    for one company. Used when user requests F29 calculation on-demand.

    Args:
        company_id: Company UUID (as string)
        period_year: Year for the F29 period
        period_month: Month for the F29 period (1-12)
        auto_calculate: Whether to auto-calculate values from tax documents (default: True)

    Returns:
        Dict with result:
        {
            "success": bool,
            "company_id": str,
            "period_year": int,
            "period_month": int,
            "created": bool,  # True if new draft was created
            "error": str (optional),
            "execution_time_seconds": float
        }

    Example:
        # Generate draft for October 2025 for specific company
        generate_f29_draft_for_company.delay(
            company_id="uuid-here",
            period_year=2025,
            period_month=10
        )
    """
    import asyncio as async_lib
    from datetime import datetime
    from app.config.database import AsyncSessionLocal

    start_time = datetime.utcnow()

    try:
        # Convert string UUID to UUID object
        company_uuid = UUID(company_id)

        logger.info(
            f"📝 [CELERY TASK] Starting F29 draft generation for company {company_id}: "
            f"period={period_year}-{period_month:02d}, auto_calculate={auto_calculate}"
        )

        async def _generate_draft():
            """Async wrapper to call service"""
            from app.services.form29 import Form29Service

            async with AsyncSessionLocal() as db:
                service = Form29Service(db)
                form29, is_new = await service.create_draft_for_period(
                    company_id=company_uuid,
                    period_year=period_year,
                    period_month=period_month,
                    created_by_user_id=None,  # System-generated
                    auto_calculate=auto_calculate
                )
                await db.commit()
                return form29, is_new

        # Run async function
        form29, is_new = async_lib.run(_generate_draft())

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"✅ [CELERY TASK] F29 draft generation completed for company {company_id}: "
            f"period={period_year}-{period_month:02d}, created={is_new}, time={execution_time:.2f}s"
        )

        return {
            "success": True,
            "company_id": company_id,
            "period_year": period_year,
            "period_month": period_month,
            "created": is_new,
            "execution_time_seconds": execution_time
        }

    except ValueError as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_msg = str(e)
        logger.warning(
            f"⚠️ [CELERY TASK] F29 draft generation validation error for company {company_id}: {error_msg}",
        )
        return {
            "success": False,
            "company_id": company_id,
            "period_year": period_year,
            "period_month": period_month,
            "created": False,
            "error": error_msg,
            "execution_time_seconds": execution_time
        }

    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"❌ [CELERY TASK] F29 draft generation failed for company {company_id}: {e}",
            exc_info=True
        )

        # Retry on certain errors
        if "database" in str(e).lower() or "connection" in str(e).lower():
            raise self.retry(exc=e)

        return {
            "success": False,
            "company_id": company_id,
            "period_year": period_year,
            "period_month": period_month,
            "created": False,
            "error": str(e),
            "execution_time_seconds": execution_time
        }
