"""
Generic Template-Driven Notification Task

Tarea genérica que procesa cualquier template de notificación.
La lógica de negocio está completamente definida en el template.

Uso:
    # En PeriodicTask, simplemente pasa el código del template:
    process_template_notification(template_code="daily_business_summary")
    process_template_notification(template_code="weekly_business_summary")
    process_template_notification(template_code="monthly_business_summary")

Configuración del Template:
    El template debe tener en su campo metadata:
    {
        "summary_config": {
            "service_method": "get_daily_summary",  # método del business_summary service
            "lookback_days": 1,                      # días a incluir en el resumen
            "date_offset": -1                        # días a restar de hoy para end_date
        }
    }

    IMPORTANTE: El horario de envío se controla mediante la Scheduled Task (crontab/interval),
    NO en el template. El template solo define QUÉ datos se envían.

Ejemplos de templates soportados:
    - daily_business_summary: Resumen diario (1 día, offset -1)
    - weekly_business_summary: Resumen semanal (7 días, offset -1)
    - monthly_business_summary: Resumen mensual (30 días, offset -1)
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN DEFAULT
# ============================================================================

DEFAULT_SUMMARY_CONFIG = {
    "service_method": "get_daily_summary",
    "lookback_days": 1,
    "date_offset": -1,
}


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def _build_whatsapp_components(
    template: Any,
    summary_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Build WhatsApp template components from template structure and summary data.

    Extracts template structure from template.extra_metadata and builds
    Meta API v21.0 components (without "name" field in parameters).
    """
    components = []

    # Get template structure
    template_structure = template.extra_metadata.get("whatsapp_template_structure", {})
    header_params = template_structure.get("header_params", [])
    body_params = template_structure.get("body_params", [])

    # Build header component
    if header_params:
        header_parameters = []
        for param_name in header_params:
            if param_name in summary_data:
                # Meta API v21.0 uses "parameter_name" for named parameters
                header_parameters.append({
                    "type": "text",
                    "parameter_name": param_name,
                    "text": str(summary_data[param_name])
                })

        if header_parameters:
            components.append({
                "type": "header",
                "parameters": header_parameters
            })

    # Build body component
    if body_params:
        body_parameters = []
        for param_name in body_params:
            if param_name in summary_data:
                # Meta API v21.0 uses "parameter_name" for named parameters
                body_parameters.append({
                    "type": "text",
                    "parameter_name": param_name,
                    "text": str(summary_data[param_name])
                })

        if body_parameters:
            components.append({
                "type": "body",
                "parameters": body_parameters
            })

    return components


async def _get_eligible_recipients(
    company: Any,
    template: Any,
    user_pref_repo: Any
) -> List[Dict[str, str]]:
    """
    Obtiene usuarios elegibles para recibir la notificación.

    Args:
        company: Empresa de la que obtener usuarios
        template: Template de notificación
        user_pref_repo: Repository de preferencias de usuario

    Returns:
        Lista de recipients con user_id y phone
    """
    # Obtener usuarios activos con teléfono
    users = await user_pref_repo.find_active_users_with_phone(company.id)

    if not users:
        logger.info(f"⏭️  No users with phone for company {company.business_name}")
        return []

    recipients = []

    for profile, session in users:
        # Verificar preferencias individuales
        preference = await user_pref_repo.find_by_user_and_company(
            user_id=profile.id,
            company_id=company.id
        )

        # Skip si el usuario deshabilitó todas las notificaciones
        if preference and not preference.notifications_enabled:
            logger.debug(f"⏭️  User {profile.id} has disabled all notifications")
            continue

        # Skip si el usuario silenció este template específico
        if preference:
            muted_templates = preference.muted_templates or []
            if str(template.id) in muted_templates:
                logger.debug(f"⏭️  User {profile.id} has muted template {template.code}")
                continue

        recipients.append({
            "user_id": str(profile.id),
            "phone": profile.phone
        })

    if not recipients:
        logger.info(
            f"⏭️  All users have muted this template for company {company.business_name}"
        )

    return recipients


async def _process_single_company(
    company: Any,
    template: Any,
    summary_config: Dict[str, Any],
    end_date: date,
    db: Any,
    business_service: Any,
    notification_service: Any,
    subscription_repo: Any,
    user_pref_repo: Any
) -> bool:
    """
    Procesa una empresa individual para el template dado.

    Args:
        company: Empresa a procesar
        template: Template de notificación
        summary_config: Configuración del resumen desde template.metadata
        end_date: Fecha fin del resumen
        db: Sesión de base de datos
        business_service: Servicio de resúmenes de negocio
        notification_service: Servicio de notificaciones
        subscription_repo: Repository de suscripciones
        user_pref_repo: Repository de preferencias de usuario

    Returns:
        True si se creó la notificación, False en caso contrario
    """
    logger.info(f"📊 Processing company: {company.business_name}")

    # 1. Verificar suscripción activa
    subscription = await subscription_repo.find_by_company_and_template(
        company_id=company.id,
        template_id=template.id,
        enabled_only=True
    )

    if not subscription:
        logger.info(f"⏭️  No active subscription for company {company.business_name}")
        return False

    # 2. Obtener usuarios elegibles
    recipients = await _get_eligible_recipients(company, template, user_pref_repo)
    if not recipients:
        return False

    # 3. Generar resumen usando el método configurado en el template
    service_method_name = summary_config.get("service_method", "get_daily_summary")

    if not hasattr(business_service, service_method_name):
        logger.error(
            f"❌ Service method '{service_method_name}' not found in business_summary service"
        )
        return False

    summary_method = getattr(business_service, service_method_name)
    summary_data = await summary_method(
        company_id=company.id,
        target_date=end_date
    )

    # 4. Crear notificación programada
    scheduled_notification = await notification_service.schedule_notification(
        db=db,
        company_id=company.id,
        template_id=template.id,
        recipients=recipients,
        message_context=summary_data,
        entity_type=template.entity_type or "business_summary",
        entity_id=None,
        reference_date=end_date,
        custom_timing=None  # Timing is controlled by the scheduled task, not the template
    )

    if scheduled_notification:
        logger.info(
            f"✅ Company {company.business_name}: "
            f"1 notification scheduled for {len(recipients)} recipients"
        )
        return True

    return False


# ============================================================================
# TAREA PRINCIPAL
# ============================================================================

@celery_app.task(
    name="notifications.process_template_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutos
)
def process_template_notification(self, template_code: str):
    """
    Tarea genérica que procesa cualquier template de notificación.

    Esta tarea es completamente agnóstica de la lógica de negocio.
    Todo está definido en el template:
    - Qué servicio llamar (service_method)
    - Cuántos días incluir (lookback_days)
    - A qué hora enviar (send_hour, send_minute)

    Para crear un nuevo tipo de resumen, solo necesitas:
    1. Crear un template con la configuración correcta en metadata
    2. Crear un PeriodicTask que llame a esta tarea con el template_code

    Args:
        template_code: Código del template a procesar (ej: "daily_business_summary")

    Returns:
        dict: Resumen de ejecución con estadísticas

    Example:
        # En PeriodicTask:
        process_template_notification(template_code="daily_business_summary")
        process_template_notification(template_code="weekly_business_summary")
    """
    logger.info(f"📊 Starting template notification processing: {template_code}")

    async def _process_notification():
        from app.config.database import AsyncSessionLocal
        from app.services.business_summary import get_business_summary_service
        from app.services.notifications import get_notification_service
        from app.infrastructure.celery.subscription_helper import get_subscribed_companies
        from app.repositories import (
            NotificationTemplateRepository,
            NotificationSubscriptionRepository,
            UserNotificationPreferenceRepository
        )
        from app.db.models import Company
        from uuid import UUID
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            # Inicializar repositories
            template_repo = NotificationTemplateRepository(db)
            subscription_repo = NotificationSubscriptionRepository(db)
            user_pref_repo = UserNotificationPreferenceRepository(db)

            # 1. Obtener el template por código
            template = await template_repo.find_by_code(template_code, active_only=True)

            if not template:
                logger.error(f"❌ Template '{template_code}' not found or inactive")
                return {
                    "success": False,
                    "error": f"Template '{template_code}' not found",
                    "companies_processed": 0,
                    "notifications_created": 0
                }

            # 2. Extraer configuración del template (o usar defaults)
            # NOTA: El campo se llama 'extra_metadata' en el modelo Python (para evitar conflicto con SQLAlchemy)
            template_metadata = template.extra_metadata if template.extra_metadata else {}
            summary_config = template_metadata.get("summary_config", {})

            # Merge con defaults
            config = {**DEFAULT_SUMMARY_CONFIG, **summary_config}

            lookback_days = config["lookback_days"]
            date_offset = config["date_offset"]

            logger.info(
                f"📋 Template config: method={config['service_method']}, "
                f"lookback={lookback_days} days, offset={date_offset}"
            )

            # 3. Calcular fechas (genérico basado en configuración)
            end_date = date.today() + timedelta(days=date_offset)
            start_date = end_date - timedelta(days=lookback_days - 1) if lookback_days > 1 else end_date

            logger.info(
                f"📅 Date range: {start_date.isoformat()} to {end_date.isoformat()}"
            )

            # 5. Get only companies with active subscription
            subscribed_companies_data = await get_subscribed_companies(db, only_active=True)

            if not subscribed_companies_data:
                logger.info("⏭️  No subscribed companies found")
                return {
                    "success": True,
                    "template_code": template_code,
                    "companies_processed": 0,
                    "notifications_created": 0,
                    "total_companies": 0,
                    "errors": [],
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }

            # Get full Company objects
            company_ids = [UUID(company_id) for company_id, _ in subscribed_companies_data]
            stmt = select(Company).where(Company.id.in_(company_ids))
            result = await db.execute(stmt)
            companies = result.scalars().all()

            logger.info(f"📋 Found {len(companies)} subscribed companies")

            # 6. Inicializar servicios
            business_service = await get_business_summary_service(db)
            notification_service = get_notification_service()

            companies_processed = 0
            notifications_created = 0
            errors = []

            # 7. Procesar cada empresa
            for company in companies:
                try:
                    success = await _process_single_company(
                        company=company,
                        template=template,
                        summary_config=config,
                        end_date=end_date,
                        db=db,
                        business_service=business_service,
                        notification_service=notification_service,
                        subscription_repo=subscription_repo,
                        user_pref_repo=user_pref_repo
                    )

                    if success:
                        notifications_created += 1
                        companies_processed += 1

                except Exception as e:
                    logger.error(
                        f"❌ Error processing company {company.business_name}: {e}",
                        exc_info=True
                    )
                    errors.append({
                        "company_id": str(company.id),
                        "company_name": company.business_name,
                        "error": str(e)
                    })

            return {
                "success": True,
                "template_code": template_code,
                "companies_processed": companies_processed,
                "notifications_created": notifications_created,
                "total_companies": len(companies),
                "errors": errors,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }

    try:
        # Run async function in sync context
        result = asyncio.run(_process_notification())

        logger.info(
            f"✅ Template notification '{template_code}' completed: "
            f"{result.get('companies_processed', 0)}/{result.get('total_companies', 0)} companies processed, "
            f"{result.get('notifications_created', 0)} notifications created"
        )

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Template '{template_code}' processed successfully",
            **result
        }

    except Exception as e:
        logger.error(
            f"❌ Error processing template notification '{template_code}': {e}",
            exc_info=True
        )

        # Retry la tarea si falla
        try:
            raise self.retry(exc=e)
        except Exception as retry_error:
            logger.error(
                f"Max retries reached for template '{template_code}': {retry_error}"
            )
            return {
                "success": False,
                "template_code": template_code,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
