"""
Celery tasks for SII document synchronization.

These tasks handle the synchronization of tax documents (purchases and sales)
from the SII website to the local database.

IMPORTANT: Keep tasks simple - delegate to services for business logic.
"""
import logging
from typing import Dict, Any

from app.infrastructure.celery import celery_app
from app.integrations.sii.exceptions import SIIUnavailableException

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="sii.sync_documents",
    max_retries=3,
    default_retry_delay=60,
)
def sync_documents(
    self,
    session_id: str = None,
    months: int = 1,
    company_id: str = None,
    month_offset: int = 0,
) -> Dict[str, Any]:
    """
    Celery task wrapper for tax documents sync (purchases and sales).

    Delegates to SIISyncService.sync_last_n_months() for business logic.

    Args:
        session_id: Optional UUID of the SII session (str format).
                    If not provided, will be found using company_id.
        months: Number of months to sync (1-12)
        company_id: Optional UUID of the company (str format).
                    If provided, will find the most recent active session for this company.
        month_offset: Number of months to skip from current month (0=current month, 1=last month, etc.)
                     Useful for parallelizing syncs across different months.

    Returns:
        Dict with sync results from service layer:
        {
            "success": bool,
            "compras": {"total": int, "nuevos": int, "actualizados": int},
            "ventas": {"total": int, "nuevos": int, "actualizados": int},
            "honorarios": {"total": int, "nuevos": int, "actualizados": int},
            "duration_seconds": float,
            "errors": int,
            "company_id": str,
            "session_id": str
        }
    """
    try:
        # Import dependencies
        import asyncio
        from uuid import UUID
        from app.dependencies import get_background_db
        from app.services.sii.sync_service import SIISyncService
        from app.db.models.session import Session
        from sqlalchemy import select

        logger.info(
            f"🚀 [CELERY TASK] Document sync started: "
            f"session_id={session_id}, company_id={company_id}, months={months}, offset={month_offset}"
        )

        # Delegate to service layer - USE SINGLE DB SESSION for entire task
        async def _sync():
            nonlocal company_id, session_id

            async with get_background_db() as db:
                # If company_id is provided but not session_id, find the most recent active session
                if company_id and not session_id:
                    logger.info(
                        f"🔍 [CELERY TASK] Finding most recent active session for company {company_id}"
                    )
                    result = await db.execute(
                        select(Session.id)
                        .where(Session.company_id == UUID(company_id))
                        .where(Session.is_active == True)
                        .order_by(Session.last_accessed_at.desc())
                        .limit(1)
                    )
                    session_row = result.first()
                    if session_row:
                        session_id = str(session_row[0])
                        logger.info(f"✅ [CELERY TASK] Found session {session_id} for company {company_id}")
                    else:
                        error_msg = f"No active session found for company {company_id}"
                        logger.error(f"❌ [CELERY TASK] {error_msg}")
                        return {
                            "success": False,
                            "error": error_msg,
                            "company_id": company_id,
                            "session_id": None
                        }

                # Ensure we have a session_id at this point
                if not session_id:
                    error_msg = "Either session_id or company_id must be provided"
                    logger.error(f"❌ [CELERY TASK] {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "company_id": company_id,
                        "session_id": None
                    }

                # Initialize service with the same DB session
                sync_service = SIISyncService(db)
                result = await sync_service.sync_last_n_months(
                    session_id=session_id,
                    months=months,
                    month_offset=month_offset,
                )
                # Commit is automatic in get_background_db()

                # Get company_id if not provided
                if not company_id:
                    session_result = await db.execute(
                        select(Session.company_id).where(Session.id == UUID(session_id))
                    )
                    company_id_row = session_result.first()
                    if company_id_row:
                        company_id = str(company_id_row[0])

                return result

        # Run async function in sync context
        result = asyncio.run(_sync())

        # Handle error results
        if not result.get("success", True):
            return result

        logger.info(
            f"✅ [CELERY TASK] Document sync completed: "
            f"compras={result['compras']['total']}, ventas={result['ventas']['total']}, "
            f"honorarios={result['honorarios']['total']}"
        )

        return {
            "success": True,
            "compras": result["compras"],
            "ventas": result["ventas"],
            "honorarios": result["honorarios"],
            "duration_seconds": result["duration_seconds"],
            "errors": len(result.get("errors", [])),
            "error_details": result.get("errors", []),
            "company_id": company_id,
            "session_id": session_id,
        }

    except SIIUnavailableException as e:
        logger.warning(f"⚠️ [CELERY TASK] SII unavailable, will retry: {e}")
        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"❌ [CELERY TASK] Document sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "company_id": company_id,
            "session_id": session_id
        }


@celery_app.task(
    bind=True,
    name="sii.sync_documents_all_companies",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def sync_documents_all_companies(
    self,
    months: int = 1,
) -> Dict[str, Any]:
    """
    Celery task to sync documents for all companies using their most recent active session.

    This task queries all companies and for each one finds the most recently accessed
    active session, then triggers sync_documents for that session.
    Useful for batch synchronization across all companies.

    Args:
        months: Number of months to sync for each company (1-12)

    Returns:
        Dict with summary results:
        {
            "success": bool,
            "total_companies": int,
            "synced": int,
            "failed": int,
            "skipped": int,
            "results": [...]
        }
    """
    try:
        logger.info(
            f"🚀 [CELERY TASK] Starting batch sync for all companies: {months} months"
        )

        # Use sync session for Celery tasks (Celery workers are synchronous)
        from app.config.database import SyncSessionLocal
        from app.db.models.company import Company
        from app.db.models.session import Session
        from sqlalchemy import select

        # Get all companies with their most recent active session
        with SyncSessionLocal() as db:
            # Get all companies
            companies_result = db.execute(
                select(Company.id, Company.business_name)
            )
            # Keep UUID objects for queries, convert to string only for display
            companies = [(company_id, name) for (company_id, name) in companies_result.all()]

            if not companies:
                logger.warning("⚠️ [CELERY TASK] No companies found")
                return {
                    "success": True,
                    "total_companies": 0,
                    "synced": 0,
                    "failed": 0,
                    "skipped": 0,
                    "message": "No companies to sync"
                }

            logger.info(f"📋 [CELERY TASK] Found {len(companies)} companies")

            # For each company, get the most recent active session
            company_sessions = []
            for company_id_uuid, company_name in companies:
                session_result = db.execute(
                    select(Session.id)
                    .where(Session.company_id == company_id_uuid)  # Use UUID for query
                    .where(Session.is_active == True)
                    .order_by(Session.last_accessed_at.desc())
                    .limit(1)
                )
                session_row = session_result.first()

                if session_row:
                    company_sessions.append({
                        "company_id": str(company_id_uuid),  # Convert to string for display
                        "company_name": company_name,
                        "session_id": str(session_row[0])
                    })
                else:
                    logger.warning(f"⚠️ [CELERY TASK] No active session found for company {company_name} ({company_id_uuid})")

        if not company_sessions:
            logger.warning("⚠️ [CELERY TASK] No companies with active sessions found")
            return {
                "success": True,
                "total_companies": len(companies),
                "synced": 0,
                "failed": 0,
                "skipped": len(companies),
                "message": "No companies with active sessions to sync"
            }

        logger.info(f"📋 [CELERY TASK] Found {len(company_sessions)} companies with active sessions")

        # Trigger sync_documents for each company's session
        results = []
        synced = 0
        failed = 0
        skipped = len(companies) - len(company_sessions)

        for company_session in company_sessions:
            company_id = company_session["company_id"]
            company_name = company_session["company_name"]
            session_id = company_session["session_id"]

            try:
                logger.info(f"🔄 [CELERY TASK] Syncing company {company_name} ({company_id}) using session {session_id}")

                # Call sync_documents task directly (synchronous call within this task)
                # Pass both session_id and company_id for better tracking
                result = sync_documents(
                    session_id=session_id,
                    months=months,
                    company_id=company_id
                )

                if result.get("success"):
                    synced += 1
                    logger.info(f"✅ [CELERY TASK] Company {company_name} synced successfully")
                else:
                    failed += 1
                    logger.error(f"❌ [CELERY TASK] Company {company_name} sync failed: {result.get('error')}")

                results.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "session_id": session_id,
                    "success": result.get("success"),
                    "compras": result.get("compras"),
                    "ventas": result.get("ventas"),
                    "honorarios": result.get("honorarios"),
                    "error": result.get("error")
                })

            except Exception as e:
                failed += 1
                logger.error(f"❌ [CELERY TASK] Exception syncing company {company_name}: {e}", exc_info=True)
                results.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "session_id": session_id,
                    "success": False,
                    "error": str(e)
                })

        logger.info(
            f"✅ [CELERY TASK] Batch sync completed: "
            f"total_companies={len(companies)}, synced={synced}, failed={failed}, skipped={skipped}"
        )

        return {
            "success": True,
            "total_companies": len(companies),
            "synced": synced,
            "failed": failed,
            "skipped": skipped,
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ [CELERY TASK] Batch sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "total_companies": 0,
            "synced": 0,
            "failed": 0,
            "skipped": 0
        }
