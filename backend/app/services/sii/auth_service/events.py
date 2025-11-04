"""
Módulo de gestión de eventos tributarios y notificaciones
"""
import logging
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)


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


async def trigger_sync_tasks(company_id: UUID) -> None:
    """
    Dispara tareas de Celery en background para sincronización

    Args:
        company_id: UUID de la compañía
    """
    # Importar tareas de Celery
    from app.infrastructure.celery.tasks.sii.documents import sync_documents
    from app.infrastructure.celery.tasks.sii.forms import sync_f29
    from app.infrastructure.celery.tasks.calendar import sync_company_calendar

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

    # 2. Disparar sincronización de documentos tributarios (últimos 3 meses)
    # Estrategia: Sincronizar cada mes por separado en diferentes workers
    # - Mes más reciente (offset=0): ejecutar inmediatamente (más importante)
    # - Mes -1 (offset=1): ejecutar con delay de 5 minutos
    # - Mes -2 (offset=2): ejecutar con delay de 5 minutos
    try:
        # Mes más reciente (offset=0) - ejecutar inmediatamente
        sync_documents.delay(
            company_id=str(company_id),
            months=1,
            month_offset=0
        )
        logger.info(
            f"[Events] sync_documents task triggered (offset=0, most recent month) "
            f"for company {company_id} - immediate execution"
        )

        # Mes -1 (offset=1) - ejecutar en 5 minutos (300 segundos)
        sync_documents.apply_async(
            kwargs={
                "company_id": str(company_id),
                "months": 1,
                "month_offset": 1
            },
            countdown=20
        )
        logger.info(
            f"[Events] sync_documents task triggered (offset=1) "
            f"for company {company_id} - delayed 5 minutes"
        )

        # Mes -2 (offset=2) - ejecutar en 5 minutos (300 segundos)
        sync_documents.apply_async(
            kwargs={
                "company_id": str(company_id),
                "months": 1,
                "month_offset": 2
            },
            countdown=40
        )
        logger.info(
            f"[Events] sync_documents task triggered (offset=2) "
            f"for company {company_id} - delayed 5 minutes"
        )
    except Exception as e:
        logger.error(f"[Events] Error triggering sync_documents: {e}")

    # 3. Disparar sincronización de formularios F29 (año actual)
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
