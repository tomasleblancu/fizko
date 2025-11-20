"""
Calendar Sync Tasks

Tareas de Celery para sincronización de calendario de eventos tributarios.

Tareas:
- sync_company_calendar: Sincroniza calendario para una empresa específica
- sync_all_companies_calendar: Sincroniza calendario para todas las empresas activas
"""
import asyncio
import logging
from typing import Dict, Any
from sqlalchemy import select

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="calendar.sync_company",
    max_retries=3,
    default_retry_delay=60
)
def sync_company_calendar(
    self,
    company_id: str
) -> Dict[str, Any]:
    """
    Sincroniza el calendario de eventos tributarios para una empresa específica

    Esta tarea:
    1. Crea eventos faltantes para los próximos periodos (mensuales/anuales)
    2. Actualiza estados de eventos existentes
    3. Gestiona el estado 'in_progress' solo para el próximo evento a vencer

    Args:
        company_id: UUID de la empresa (como string)

    Returns:
        Dict con resultado de la sincronización

    Example:
        >>> from app.infrastructure.celery.tasks.calendar import sync_company_calendar
        >>> result = sync_company_calendar.delay("085ed9db-d666-4a98-bb05-13a79257e9c9")
    """
    logger.info(
        f"🚀 [CELERY TASK] Calendar sync started for company {company_id}"
    )

    # Delegate to service layer
    async def _sync_calendar():
        from app.config.database import AsyncSessionLocal
        from app.services.calendar import CalendarService

        async with AsyncSessionLocal() as db:
            service = CalendarService(db)
            return await service.sync_company_calendar(company_id=company_id)

    try:
        # Run async function in sync context
        result = asyncio.run(_sync_calendar())

        logger.info(
            f"✅ [CELERY TASK] Calendar sync completed for company {company_id}: "
            f"{result['total_created']} created, {result['total_updated']} updated"
        )

        return {
            "success": True,
            "company_id": company_id,
            **result
        }

    except ValueError as e:
        error_msg = str(e)
        logger.error(f"❌ [CELERY TASK] Calendar sync validation error: {error_msg}")
        return {
            "success": False,
            "company_id": company_id,
            "error": error_msg
        }

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Calendar sync failed for company {company_id}: {e}",
            exc_info=True
        )

        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        return {
            "success": False,
            "company_id": company_id,
            "error": str(e)
        }


@celery_app.task(
    bind=True,
    name="calendar.sync_all_companies",
    max_retries=1
)
def sync_all_companies_calendar(self) -> Dict[str, Any]:
    """
    Sincroniza el calendario para TODAS las empresas activas

    Esta tarea batch:
    1. Obtiene todas las empresas activas
    2. Para cada empresa, ejecuta la sincronización de calendario
    3. Recopila resultados y estadísticas

    Returns:
        Dict con resumen de sincronización batch

    Example:
        >>> from app.infrastructure.celery.tasks.calendar import sync_all_companies_calendar
        >>> result = sync_all_companies_calendar.delay()
    """
    logger.info("🚀 [CELERY TASK] Batch calendar sync started for all companies")

    async def _sync_all():
        from app.config.database import AsyncSessionLocal
        from app.infrastructure.celery.subscription_helper import get_subscribed_companies
        from app.db.models import Company
        from app.services.calendar import CalendarService
        from uuid import UUID

        async with AsyncSessionLocal() as db:
            # Obtener empresas con suscripción activa
            subscribed_companies_data = await get_subscribed_companies(db, only_active=True)

            if not subscribed_companies_data:
                logger.info("⏭️  No subscribed companies found")
                return {
                    "total_companies": 0,
                    "synced": 0,
                    "failed": 0,
                    "skipped": 0,
                    "results": []
                }

            # Get full Company objects
            company_ids = [UUID(company_id) for company_id, _ in subscribed_companies_data]
            stmt = select(Company).where(Company.id.in_(company_ids))
            result = await db.execute(stmt)
            companies = result.scalars().all()

            logger.info(f"📊 Found {len(companies)} subscribed companies")

            synced = 0
            failed = 0
            skipped = 0
            results = []

            service = CalendarService(db)

            for company in companies:
                try:
                    logger.info(f"🔄 Syncing calendar for company: {company.business_name}")

                    result = await service.sync_company_calendar(company_id=company.id)

                    synced += 1
                    results.append({
                        "company_id": str(company.id),
                        "company_name": company.business_name,
                        "success": True,
                        "created": result['total_created'],
                        "updated": result['total_updated'],
                        "error": None
                    })

                    logger.info(
                        f"✅ Company {company.business_name}: "
                        f"{result['total_created']} created, {result['total_updated']} updated"
                    )

                except ValueError as e:
                    # Empresa sin eventos activos configurados - es esperado
                    skipped += 1
                    logger.warning(
                        f"⚠️ Company {company.business_name} skipped: {e}"
                    )
                    results.append({
                        "company_id": str(company.id),
                        "company_name": company.business_name,
                        "success": False,
                        "created": 0,
                        "updated": 0,
                        "error": str(e),
                        "skipped": True
                    })

                except Exception as e:
                    failed += 1
                    logger.error(
                        f"❌ Company {company.business_name} failed: {e}",
                        exc_info=True
                    )
                    results.append({
                        "company_id": str(company.id),
                        "company_name": company.business_name,
                        "success": False,
                        "created": 0,
                        "updated": 0,
                        "error": str(e),
                        "skipped": False
                    })

            return {
                "total_companies": len(companies),
                "synced": synced,
                "failed": failed,
                "skipped": skipped,
                "results": results
            }

    try:
        result = asyncio.run(_sync_all())

        logger.info(
            f"✅ [CELERY TASK] Batch calendar sync completed: "
            f"total={result['total_companies']}, synced={result['synced']}, "
            f"failed={result['failed']}, skipped={result['skipped']}"
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Batch calendar sync failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e)
        }
