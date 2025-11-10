"""
Celery tasks for SII form processing.

These tasks handle the processing and synchronization of tax forms (F29, F22, etc.)
from the SII website to the local database.

IMPORTANT: Keep tasks simple - delegate to services for business logic.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from app.infrastructure.celery import celery_app
from app.integrations.sii.exceptions import SIIUnavailableException

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="sii.sync_f29",
    max_retries=3,
    default_retry_delay=60,
)
def sync_f29(
    self,
    session_id: str = None,
    year: int = None,
    company_id: str = None,
) -> Dict[str, Any]:
    """
    Celery task wrapper for F29 form synchronization.

    Syncs F29 forms from SII for a specific year. If year is not provided,
    uses the current year.

    Args:
        session_id: Optional UUID of the SII session (str format).
                    If not provided, will be found using company_id.
        year: Year to sync (e.g., 2024). If not provided, uses current year.
        company_id: Optional UUID of the company (str format).
                    If provided, will find the most recent active session for this company.

    Returns:
        Dict with sync results:
        {
            "success": bool,
            "forms_synced": int,
            "year": int,
            "company_id": str,
            "session_id": str,
            "message": str
        }
    """
    try:
        # Import dependencies
        import asyncio
        from uuid import UUID
        from app.dependencies import get_background_db
        from app.services.sii import SIIService
        from app.db.models.session import Session
        from sqlalchemy import select

        # Default year to current year if not provided
        if not year:
            year = datetime.now().year
            logger.info(f"📅 [CELERY TASK] No year provided, using current year: {year}")

        logger.info(
            f"🚀 [CELERY TASK] F29 sync started: year={year}, "
            f"session_id={session_id}, company_id={company_id}"
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
                            "session_id": None,
                            "year": year
                        }

                # Ensure we have a session_id at this point
                if not session_id:
                    error_msg = "Either session_id or company_id must be provided"
                    logger.error(f"❌ [CELERY TASK] {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "company_id": company_id,
                        "session_id": None,
                        "year": year
                    }

                # Initialize service with the same DB session
                service = SIIService(db)

                # Extract F29 forms from SII with incremental saving
                # El servicio ahora guarda cada formulario inmediatamente después de extraer su id_interno_sii
                formularios = await service.extract_f29_lista(
                    session_id=session_id,
                    anio=str(year),
                    company_id=company_id  # Necesario para guardado incremental
                )

                # Los formularios ya fueron guardados incrementalmente durante la extracción
                # Solo retornar el resultado

                if not formularios:
                    logger.info(f"ℹ️ [CELERY TASK] No F29 forms found for year {year}")
                    return {
                        "success": True,
                        "forms_synced": 0,
                        "company_id": company_id,
                        "message": f"No se encontraron formularios F29 para el año {year}"
                    }

                logger.info(
                    f"✅ [CELERY TASK] F29 extraction completed: {len(formularios)} formularios "
                    f"(guardados incrementalmente)"
                )

                return {
                    "success": True,
                    "forms_synced": len(formularios),
                    "company_id": company_id,
                    "message": f"{len(formularios)} formularios F29 sincronizados incrementalmente"
                }

        # Run async function in sync context
        result = asyncio.run(_sync())

        # Handle error results from _sync
        if not result.get("success"):
            return result

        logger.info(
            f"✅ [CELERY TASK] F29 sync completed: {result['forms_synced']} forms synced"
        )

        return {
            "success": True,
            "forms_synced": result["forms_synced"],
            "year": year,
            "company_id": result["company_id"],
            "session_id": session_id,
            "message": result["message"]
        }

    except SIIUnavailableException as e:
        logger.warning(f"⚠️ [CELERY TASK] SII unavailable, will retry: {e}")
        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"❌ [CELERY TASK] F29 sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "company_id": company_id,
            "session_id": session_id,
            "year": year
        }


@celery_app.task(
    bind=True,
    name="sii.sync_f29_all_companies",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def sync_f29_all_companies(
    self,
    year: int = None,
) -> Dict[str, Any]:
    """
    Celery task to sync F29 forms for all companies using their most recent active session.

    This task queries all companies and for each one finds the most recently accessed
    active session, then triggers sync_f29 for that session.
    Useful for batch synchronization across all companies.

    Args:
        year: Year to sync for each company. If not provided, uses current year.

    Returns:
        Dict with summary results:
        {
            "success": bool,
            "year": int,
            "total_companies": int,
            "synced": int,
            "failed": int,
            "skipped": int,
            "results": [...]
        }
    """
    try:
        # Default year to current year if not provided
        if not year:
            year = datetime.now().year
            logger.info(f"📅 [CELERY TASK] No year provided, using current year: {year}")

        logger.info(
            f"🚀 [CELERY TASK] Starting batch F29 sync for all companies: year={year}"
        )

        # Get companies with active subscriptions using async helper
        import asyncio as async_lib
        from app.config.database import AsyncSessionLocal
        from app.infrastructure.celery.subscription_helper import get_subscribed_companies
        from app.db.models.session import Session
        from sqlalchemy import select

        # Get subscribed companies
        async def _get_companies_and_sessions():
            async with AsyncSessionLocal() as db:
                # Get only companies with active subscriptions
                companies = await get_subscribed_companies(db, only_active=True)

                if not companies:
                    return []

                logger.info(f"📋 [CELERY TASK] Found {len(companies)} companies with active subscriptions")

                # For each company, get the most recent active session
                company_sessions = []
                for company_id_uuid, company_name in companies:
                    session_result = await db.execute(
                        select(Session.id)
                        .where(Session.company_id == company_id_uuid)
                        .where(Session.is_active == True)
                        .order_by(Session.last_accessed_at.desc())
                        .limit(1)
                    )
                    session_row = session_result.first()

                    if session_row:
                        company_sessions.append({
                            "company_id": str(company_id_uuid),
                            "company_name": company_name,
                            "session_id": str(session_row[0])
                        })
                    else:
                        logger.warning(f"⚠️ [CELERY TASK] No active session found for company {company_name} ({company_id_uuid})")

                return company_sessions

        company_sessions = async_lib.run(_get_companies_and_sessions())

        if not company_sessions:
            logger.warning("⚠️ [CELERY TASK] No subscribed companies with active sessions found")
            return {
                "success": True,
                "year": year,
                "total_companies": 0,
                "synced": 0,
                "failed": 0,
                "skipped": 0,
                "message": "No subscribed companies with active sessions to sync"
            }

        logger.info(f"📋 [CELERY TASK] Found {len(company_sessions)} subscribed companies with active sessions")

        # Trigger sync_f29 for each company's session
        results = []
        synced = 0
        failed = 0
        skipped = 0  # All non-subscribed companies are already filtered out

        for company_session in company_sessions:
            company_id = company_session["company_id"]
            company_name = company_session["company_name"]
            session_id = company_session["session_id"]

            try:
                logger.info(f"🔄 [CELERY TASK] Syncing F29 for company {company_name} ({company_id}) using session {session_id}")

                # Call sync_f29 task directly (synchronous call within this task)
                result = sync_f29(
                    session_id=session_id,
                    year=year,
                    company_id=company_id
                )

                if result.get("success"):
                    synced += 1
                    logger.info(f"✅ [CELERY TASK] Company {company_name} F29 synced successfully: {result.get('forms_synced')} forms")
                else:
                    failed += 1
                    logger.error(f"❌ [CELERY TASK] Company {company_name} F29 sync failed: {result.get('error')}")

                results.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "session_id": session_id,
                    "success": result.get("success"),
                    "forms_synced": result.get("forms_synced", 0),
                    "error": result.get("error")
                })

            except Exception as e:
                failed += 1
                logger.error(f"❌ [CELERY TASK] Exception syncing F29 for company {company_name}: {e}", exc_info=True)
                results.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "session_id": session_id,
                    "success": False,
                    "forms_synced": 0,
                    "error": str(e)
                })

        logger.info(
            f"✅ [CELERY TASK] Batch F29 sync completed: "
            f"total_companies={len(company_sessions)}, synced={synced}, failed={failed}, skipped={skipped}"
        )

        return {
            "success": True,
            "year": year,
            "total_companies": len(company_sessions),
            "synced": synced,
            "failed": failed,
            "skipped": skipped,
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ [CELERY TASK] Batch F29 sync failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "year": year,
            "total_companies": 0,
            "synced": 0,
            "failed": 0,
            "skipped": 0
        }


@celery_app.task(
    bind=True,
    name="sii.download_single_f29_pdf",
    max_retries=2,
    default_retry_delay=30,
)
def download_single_f29_pdf(
    self,
    download_id: str,
    session_id: str
) -> Dict[str, Any]:
    """
    Celery task para descargar el PDF de un solo formulario F29.

    Esta tarea se dispara automáticamente después de guardar cada F29
    con id_interno_sii durante la sincronización incremental.

    Args:
        download_id: UUID del registro Form29SIIDownload (str format)
        session_id: UUID de la sesión SII para autenticación (str format)

    Returns:
        Dict con resultado de descarga:
        {
            "success": bool,
            "download_id": str,
            "folio": str,
            "url": str (si éxito),
            "error": str (si falla)
        }
    """
    try:
        import asyncio
        from app.dependencies import get_background_db
        from app.services.sii import SIIService

        logger.info(
            f"📥 [CELERY TASK] Single F29 PDF download started: "
            f"download_id={download_id}, session_id={session_id}"
        )

        # Delegate to service layer
        async def _download_single_pdf():
            async with get_background_db() as db:
                service = SIIService(db)
                result = await service.download_and_save_f29_pdf(
                    download_id=download_id,
                    session_id=session_id
                )
                return result

        # Run async function in sync context
        result = asyncio.run(_download_single_pdf())

        # Log result
        if result.get("success"):
            logger.info(
                f"✅ [CELERY TASK] PDF downloaded successfully: "
                f"download_id={download_id}, url={result.get('url')}"
            )
        else:
            logger.error(
                f"❌ [CELERY TASK] PDF download failed: "
                f"download_id={download_id}, error={result.get('error')}"
            )

        return {
            "success": result.get("success", False),
            "download_id": download_id,
            "url": result.get("url"),
            "error": result.get("error")
        }

    except SIIUnavailableException as e:
        logger.warning(f"⚠️ [CELERY TASK] SII unavailable, will retry: {e}")
        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"❌ [CELERY TASK] Single PDF download failed: {e}", exc_info=True)
        return {
            "success": False,
            "download_id": download_id,
            "error": str(e)
        }


@celery_app.task(
    bind=True,
    name="sii.sync_f29_pdfs_missing",
    max_retries=3,
    default_retry_delay=60,
)
def sync_f29_pdfs_missing(
    self,
    session_id: str = None,
    company_id: str = None,
    max_per_company: int = 10,
) -> Dict[str, Any]:
    """
    Celery task to download missing F29 PDFs for a specific company.

    Downloads PDFs for all F29 forms that have:
    - sii_folio (registered folio)
    - sii_id_interno (internal code required for download)
    - NO PDF downloaded yet (pdf_download_status != 'downloaded')

    Args:
        session_id: Optional UUID of the SII session (str format).
                    If not provided, will be found using company_id.
        company_id: Optional UUID of the company (str format).
                    If provided, will find the most recent active session for this company.
        max_per_company: Maximum number of PDFs to download per company (default: 10)

    Returns:
        Dict with download results:
        {
            "success": bool,
            "company_id": str,
            "session_id": str,
            "total_pending": int,
            "downloaded": int,
            "failed": int,
            "errors": [...]
        }
    """
    try:
        # Import dependencies
        import asyncio
        from app.dependencies import get_background_db
        from app.services.sii import SIIService

        logger.info(
            f"🚀 [CELERY TASK] F29 PDF download started: "
            f"session_id={session_id}, company_id={company_id}, max={max_per_company}"
        )

        # Delegate ALL logic to service layer
        async def _download_pdfs():
            async with get_background_db() as db:
                service = SIIService(db)
                return await service.download_f29_pdfs_for_session(
                    session_id=session_id,
                    company_id=company_id,
                    max_per_company=max_per_company
                )

        # Run async function in sync context
        result = asyncio.run(_download_pdfs())

        # Log result
        if result.get("success"):
            logger.info(
                f"✅ [CELERY TASK] F29 PDF download completed: "
                f"downloaded={result['downloaded']}, failed={result['failed']}"
            )
        else:
            logger.error(
                f"❌ [CELERY TASK] F29 PDF download failed: {result.get('error')}"
            )

        return result

    except SIIUnavailableException as e:
        logger.warning(f"⚠️ [CELERY TASK] SII unavailable, will retry: {e}")
        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"❌ [CELERY TASK] F29 PDF download failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "company_id": company_id,
            "session_id": session_id,
            "total_pending": 0,
            "downloaded": 0,
            "failed": 0,
            "errors": []
        }


@celery_app.task(
    bind=True,
    name="sii.sync_f29_pdfs_missing_all_companies",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def sync_f29_pdfs_missing_all_companies(
    self,
    max_per_company: int = 10,
) -> Dict[str, Any]:
    """
    Celery task to download missing F29 PDFs for all companies.

    For each company, downloads PDFs for F29 forms that have:
    - sii_folio (registered folio)
    - sii_id_interno (internal code required for download)
    - NO PDF downloaded yet (pdf_download_status != 'downloaded')

    Args:
        max_per_company: Maximum number of PDFs to download per company (default: 10)

    Returns:
        Dict with summary results:
        {
            "success": bool,
            "max_per_company": int,
            "total_companies": int,
            "processed": int,
            "skipped": int,
            "total_pdfs_downloaded": int,
            "total_pdfs_failed": int,
            "results": [...]
        }
    """
    try:
        logger.info(
            f"🚀 [CELERY TASK] Starting batch F29 PDF download for all companies: max_per_company={max_per_company}"
        )

        # Get companies with active subscriptions using async helper
        import asyncio as async_lib
        from app.config.database import AsyncSessionLocal
        from app.infrastructure.celery.subscription_helper import get_subscribed_companies
        from app.db.models.session import Session
        from sqlalchemy import select

        # Get subscribed companies
        async def _get_companies_and_sessions():
            async with AsyncSessionLocal() as db:
                # Get only companies with active subscriptions
                companies = await get_subscribed_companies(db, only_active=True)

                if not companies:
                    return []

                logger.info(f"📋 [CELERY TASK] Found {len(companies)} companies with active subscriptions")

                # For each company, get the most recent active session
                company_sessions = []
                for company_id_uuid, company_name in companies:
                    session_result = await db.execute(
                        select(Session.id)
                        .where(Session.company_id == company_id_uuid)
                        .where(Session.is_active == True)
                        .order_by(Session.last_accessed_at.desc())
                        .limit(1)
                    )
                    session_row = session_result.first()

                    if session_row:
                        company_sessions.append({
                            "company_id": str(company_id_uuid),
                            "company_name": company_name,
                            "session_id": str(session_row[0])
                        })
                    else:
                        logger.warning(f"⚠️ [CELERY TASK] No active session found for company {company_name} ({company_id_uuid})")

                return company_sessions

        company_sessions = async_lib.run(_get_companies_and_sessions())

        if not company_sessions:
            logger.warning("⚠️ [CELERY TASK] No subscribed companies with active sessions found")
            return {
                "success": True,
                "max_per_company": max_per_company,
                "total_companies": 0,
                "processed": 0,
                "skipped": 0,
                "total_pdfs_downloaded": 0,
                "total_pdfs_failed": 0,
                "message": "No subscribed companies with active sessions to process"
            }

        logger.info(f"📋 [CELERY TASK] Found {len(company_sessions)} subscribed companies with active sessions")

        # Download PDFs for each company's session
        results = []
        processed = 0
        skipped = 0  # All non-subscribed companies are already filtered out
        total_pdfs_downloaded = 0
        total_pdfs_failed = 0

        for company_session in company_sessions:
            company_id = company_session["company_id"]
            company_name = company_session["company_name"]
            session_id = company_session["session_id"]

            try:
                logger.info(
                    f"🔄 [CELERY TASK] Downloading F29 PDFs for company {company_name} ({company_id}) "
                    f"using session {session_id}"
                )

                # Call sync_f29_pdfs_missing task directly (synchronous call within this task)
                result = sync_f29_pdfs_missing(
                    session_id=session_id,
                    company_id=company_id,
                    max_per_company=max_per_company
                )

                if result.get("success"):
                    processed += 1
                    downloaded = result.get("downloaded", 0)
                    failed = result.get("failed", 0)
                    total_pdfs_downloaded += downloaded
                    total_pdfs_failed += failed

                    logger.info(
                        f"✅ [CELERY TASK] Company {company_name}: "
                        f"downloaded={downloaded}, failed={failed}"
                    )
                else:
                    # Even if task failed, count as processed
                    processed += 1
                    logger.error(
                        f"❌ [CELERY TASK] Company {company_name} PDF download failed: {result.get('error')}"
                    )

                results.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "session_id": session_id,
                    "success": result.get("success"),
                    "total_pending": result.get("total_pending", 0),
                    "downloaded": result.get("downloaded", 0),
                    "failed": result.get("failed", 0),
                    "error": result.get("error")
                })

            except Exception as e:
                processed += 1
                logger.error(
                    f"❌ [CELERY TASK] Exception downloading F29 PDFs for company {company_name}: {e}",
                    exc_info=True
                )
                results.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "session_id": session_id,
                    "success": False,
                    "total_pending": 0,
                    "downloaded": 0,
                    "failed": 0,
                    "error": str(e)
                })

        logger.info(
            f"✅ [CELERY TASK] Batch F29 PDF download completed: "
            f"total_companies={len(company_sessions)}, processed={processed}, skipped={skipped}, "
            f"total_pdfs_downloaded={total_pdfs_downloaded}, total_pdfs_failed={total_pdfs_failed}"
        )

        return {
            "success": True,
            "max_per_company": max_per_company,
            "total_companies": len(company_sessions),
            "processed": processed,
            "skipped": skipped,
            "total_pdfs_downloaded": total_pdfs_downloaded,
            "total_pdfs_failed": total_pdfs_failed,
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ [CELERY TASK] Batch F29 PDF download failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "max_per_company": max_per_company,
            "total_companies": 0,
            "processed": 0,
            "skipped": 0,
            "total_pdfs_downloaded": 0,
            "total_pdfs_failed": 0
        }
