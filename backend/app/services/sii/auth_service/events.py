"""
Módulo de gestión de eventos tributarios y notificaciones
"""
import logging
from datetime import datetime, date
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


def calculate_months_since_start(start_date: Optional[date]) -> int:
    """
    Calcula cuántos meses sincronizar desde la fecha de inicio de actividades.

    Args:
        start_date: Fecha de inicio de actividades de la empresa

    Returns:
        Número de meses a sincronizar (mínimo 3, máximo 24)
    """
    if not start_date:
        logger.warning("[Events] No start_of_activities_date available, using default 12 months")
        return 12  # Default conservador

    today = datetime.utcnow().date()
    months = (today.year - start_date.year) * 12 + (today.month - start_date.month)

    # Limitar entre 3 y 24 meses para evitar syncs muy largos
    months_to_sync = max(3, min(months, 24))

    logger.info(
        f"[Events] Company started on {start_date.isoformat()}, "
        f"calculated {months} months of history, "
        f"will sync {months_to_sync} months (capped at 3-24)"
    )

    return months_to_sync


async def activate_mandatory_events(company_id: UUID) -> None:
    """
    Dispara tarea Celery para activar eventos tributarios obligatorios.

    Esta función NO espera a que se complete la activación.
    La activación se ejecuta en background mediante Celery.

    Args:
        company_id: UUID de la compañía

    Note:
        Los eventos se activan de forma asíncrona. Si falla, Celery reintentará
        automáticamente hasta 3 veces.
    """
    try:
        from app.infrastructure.celery.tasks.calendar import activate_mandatory_events_task

        logger.info(
            f"[Events] 🚀 Dispatching mandatory events activation task for company {company_id}"
        )

        # Disparar tarea Celery en background
        activate_mandatory_events_task.delay(
            company_id=str(company_id)
        )

        logger.info(
            f"[Events] ✅ Mandatory events task dispatched successfully"
        )

    except Exception as e:
        # No interrumpir el flujo si falla el dispatch
        logger.error(
            f"[Events] ❌ Error dispatching mandatory events task: {e}",
            exc_info=True
        )


async def assign_auto_notifications(
    company_id: UUID,
    is_new_company: bool
) -> None:
    """
    Dispara tarea Celery para asignar notificaciones automáticas.

    Esta función NO espera a que se complete la asignación.
    La asignación se ejecuta en background mediante Celery.

    Args:
        company_id: UUID de la compañía
        is_new_company: Si es una empresa recién creada (True) o existente (False)

    Note:
        Las notificaciones se asignan de forma asíncrona. Si falla, Celery reintentará
        automáticamente hasta 3 veces.
    """
    try:
        from app.infrastructure.celery.tasks.calendar import assign_auto_notifications_task

        logger.info(
            f"[Events] 🚀 Dispatching auto-notifications assignment task for company {company_id}"
        )

        # Disparar tarea Celery en background
        assign_auto_notifications_task.delay(
            company_id=str(company_id),
            is_new_company=is_new_company
        )

        logger.info(
            f"[Events] ✅ Auto-notifications task dispatched successfully"
        )

    except Exception as e:
        # No interrumpir el flujo si falla el dispatch
        logger.error(
            f"[Events] ❌ Error dispatching auto-notifications task: {e}",
            exc_info=True
        )


async def trigger_sync_tasks(company_id: UUID, company_tax_info=None) -> None:
    """
    Dispara tareas de Celery en background para sincronización inteligente.

    Nueva estrategia (3 syncs):
    1. Mes actual → inmediato, cola 'default' (rápido)
    2. Mes anterior → delay 20s, cola 'default' (rápido)
    3. Historia completa → delay 40s, cola 'low' (lento), basado en fecha de inicio

    Args:
        company_id: UUID de la compañía
        company_tax_info: CompanyTaxInfo opcional (para evitar query adicional)
    """
    # Importar tareas de Celery
    from app.infrastructure.celery.tasks.sii.documents import sync_documents
    from app.infrastructure.celery.tasks.sii.forms import sync_f29
    from app.infrastructure.celery.tasks.calendar import sync_company_calendar

    # Si no se provee company_tax_info, obtenerlo de la DB
    if company_tax_info is None:
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select
        from app.db.models import CompanyTaxInfo
        from app.config.database import get_db

        async with get_db() as db:
            stmt = select(CompanyTaxInfo).where(CompanyTaxInfo.company_id == company_id)
            result = await db.execute(stmt)
            company_tax_info = result.scalar_one_or_none()

    # Calcular meses a sincronizar basado en fecha de inicio
    start_date = company_tax_info.start_of_activities_date if company_tax_info else None
    historical_months = calculate_months_since_start(start_date)

    # 1. Disparar sincronización de calendario (eventos tributarios)
    try:
        sync_company_calendar.delay(company_id=str(company_id))
        logger.info(
            f"[Events] sync_company_calendar task triggered "
            f"for company {company_id}"
        )
    except Exception as e:
        logger.error(
            f"[Events] Error triggering sync_company_calendar: {e}"
        )

    # 2. Disparar sincronización de documentos tributarios (NUEVA ESTRATEGIA)
    # Sync 1: Mes actual (offset=0) → inmediato, cola 'default' (rápido)
    # Sync 2: Mes anterior (offset=1) → delay 20s, cola 'default' (rápido)
    # Sync 3: Historia completa → delay 40s, cola 'low' (lento), basado en fecha inicio
    try:
        # Sync 1: Mes actual (offset=0) - inmediato en cola 'default'
        sync_documents.apply_async(
            kwargs={
                "company_id": str(company_id),
                "months": 1,
                "month_offset": 0
            },
            queue="default"  # Cola rápida para onboarding
        )
        logger.info(
            f"[Events] 📥 Sync 1/3: Current month (offset=0) - "
            f"immediate on 'default' queue"
        )

        # Sync 2: Mes anterior (offset=1) - delay 20s en cola 'default'
        sync_documents.apply_async(
            kwargs={
                "company_id": str(company_id),
                "months": 1,
                "month_offset": 1
            },
            countdown=5,
            queue="default"  # Cola rápida para onboarding
        )
        logger.info(
            f"[Events] 📥 Sync 2/3: Previous month (offset=1) - "
            f"delayed 20s on 'default' queue"
        )

        # Sync 3: Historia completa (desde offset=2, un mes a la vez)
        # Dispara un task por cada mes histórico en cola 'low'
        for i in range(historical_months):
            month_offset = 2 + i  # Empieza desde offset=2 (ya tenemos 0 y 1)
            delay = 10 + (i * 5)  # Stagger: 10s, 15s, 20s, 25s, ...

            sync_documents.apply_async(
                kwargs={
                    "company_id": str(company_id),
                    "months": 1,  # Un mes a la vez
                    "month_offset": month_offset
                },
                countdown=delay,
                queue="low"  # Cola lenta para historia
            )

        logger.info(
            f"[Events] 📥 Sync 3/3: Historical data ({historical_months} individual tasks, "
            f"offset 2-{2 + historical_months - 1}) - staggered 10s-{10 + (historical_months - 1) * 5}s on 'low' queue"
        )
    except Exception as e:
        logger.error(f"[Events] ❌ Error triggering sync_documents: {e}")

    # 3. Disparar sincronización de formularios F29 (año actual)
    # NOTA: F29 se mantiene en cola 'low' (worker SLOW) según task_routes en config.py
    try:
        current_year = datetime.utcnow().year
        sync_f29.delay(
            company_id=str(company_id),
            year=current_year
        )
        logger.info(
            f"[Events] sync_f29 task triggered for company {company_id}, "
            f"year {current_year}"
        )
    except Exception as e:
        logger.error(f"[Events] Error triggering sync_f29: {e}")
