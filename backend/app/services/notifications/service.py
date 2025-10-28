"""
Servicio de Notificaciones por WhatsApp para Fizko
Gestiona la creación, programación y envío de notificaciones
"""
import logging
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    NotificationTemplate,
    NotificationSubscription,
    ScheduledNotification,
    NotificationHistory,
    UserNotificationPreference,
    CalendarEvent,
    Company,
    Profile,
)
from app.services.whatsapp.service import WhatsAppService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio de alto nivel para gestión de notificaciones.
    Maneja la creación, programación y envío de notificaciones por WhatsApp.
    """

    def __init__(self, whatsapp_service: WhatsAppService):
        """
        Inicializa el servicio de notificaciones.

        Args:
            whatsapp_service: Instancia del servicio de WhatsApp
        """
        self.whatsapp_service = whatsapp_service

    # ========== Templates ==========

    async def get_template(
        self,
        db: AsyncSession,
        template_id: Optional[UUID] = None,
        code: Optional[str] = None,
    ) -> Optional[NotificationTemplate]:
        """
        Obtiene un template por ID o código.

        Args:
            db: Sesión de base de datos
            template_id: ID del template
            code: Código del template

        Returns:
            NotificationTemplate o None si no existe
        """
        if template_id:
            result = await db.execute(
                select(NotificationTemplate).where(NotificationTemplate.id == template_id)
            )
        elif code:
            result = await db.execute(
                select(NotificationTemplate).where(NotificationTemplate.code == code)
            )
        else:
            raise ValueError("Se requiere template_id o code")

        return result.scalar_one_or_none()

    async def list_templates(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        entity_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[NotificationTemplate]:
        """
        Lista templates de notificaciones con filtros opcionales.

        Args:
            db: Sesión de base de datos
            category: Filtrar por categoría
            entity_type: Filtrar por tipo de entidad
            is_active: Filtrar por estado

        Returns:
            Lista de templates
        """
        query = select(NotificationTemplate)

        if category:
            query = query.where(NotificationTemplate.category == category)
        if entity_type:
            query = query.where(NotificationTemplate.entity_type == entity_type)
        if is_active is not None:
            query = query.where(NotificationTemplate.is_active == is_active)

        query = query.order_by(NotificationTemplate.category, NotificationTemplate.name)

        result = await db.execute(query)
        return list(result.scalars().all())

    # ========== Subscriptions ==========

    async def subscribe_company(
        self,
        db: AsyncSession,
        company_id: UUID,
        template_id: UUID,
        custom_timing: Optional[Dict] = None,
        custom_message: Optional[str] = None,
        is_enabled: bool = True,
    ) -> NotificationSubscription:
        """
        Suscribe una empresa a una notificación.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            template_id: ID del template
            custom_timing: Configuración de timing personalizada (opcional)
            custom_message: Mensaje personalizado (opcional)
            is_enabled: Si la suscripción está activa

        Returns:
            NotificationSubscription creada o actualizada
        """
        # Verificar si ya existe
        result = await db.execute(
            select(NotificationSubscription).where(
                and_(
                    NotificationSubscription.company_id == company_id,
                    NotificationSubscription.notification_template_id == template_id,
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            # Actualizar existente
            subscription.is_enabled = is_enabled
            if custom_timing:
                subscription.custom_timing_config = custom_timing
            if custom_message:
                subscription.custom_message_template = custom_message
            subscription.updated_at = datetime.utcnow()
        else:
            # Crear nueva
            subscription = NotificationSubscription(
                company_id=company_id,
                notification_template_id=template_id,
                custom_timing_config=custom_timing,
                custom_message_template=custom_message,
                is_enabled=is_enabled,
            )
            db.add(subscription)

        await db.commit()
        await db.refresh(subscription)

        logger.info(f"✅ Company {company_id} suscrita a template {template_id}")
        return subscription

    async def unsubscribe_company(
        self,
        db: AsyncSession,
        company_id: UUID,
        template_id: UUID,
    ) -> bool:
        """
        Desuscribe una empresa de una notificación.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            template_id: ID del template

        Returns:
            True si se desuscribió exitosamente
        """
        result = await db.execute(
            select(NotificationSubscription).where(
                and_(
                    NotificationSubscription.company_id == company_id,
                    NotificationSubscription.notification_template_id == template_id,
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.is_enabled = False
            subscription.updated_at = datetime.utcnow()
            await db.commit()
            logger.info(f"🔕 Company {company_id} desuscrita de template {template_id}")
            return True

        return False

    async def get_company_subscriptions(
        self,
        db: AsyncSession,
        company_id: UUID,
        is_enabled: Optional[bool] = None,
    ) -> List[NotificationSubscription]:
        """
        Obtiene las suscripciones de una empresa.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            is_enabled: Filtrar por estado (opcional)

        Returns:
            Lista de suscripciones
        """
        query = select(NotificationSubscription).where(
            NotificationSubscription.company_id == company_id
        )

        if is_enabled is not None:
            query = query.where(NotificationSubscription.is_enabled == is_enabled)

        result = await db.execute(query)
        return list(result.scalars().all())

    # ========== Scheduling ==========

    def _render_message(self, template: str, context: Dict[str, Any]) -> str:
        """
        Renderiza un mensaje reemplazando variables.

        Args:
            template: Template del mensaje con variables {{variable}}
            context: Diccionario con valores de variables

        Returns:
            Mensaje renderizado
        """
        message = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            message = message.replace(placeholder, str(value))
        return message

    def _calculate_scheduled_time(
        self,
        timing_config: Dict,
        reference_date: Optional[datetime] = None,
    ) -> datetime:
        """
        Calcula el momento de envío basado en la configuración de timing.

        Args:
            timing_config: Configuración de timing del template
            reference_date: Fecha de referencia (ej: due_date del evento)

        Returns:
            Timestamp de cuándo debe enviarse la notificación
        """
        timing_type = timing_config.get("type", "immediate")

        if timing_type == "immediate":
            return datetime.utcnow()

        elif timing_type == "relative":
            # Relativo a una fecha de referencia (ej: -1 día del evento)
            if not reference_date:
                raise ValueError("reference_date requerida para timing relativo")

            offset_days = timing_config.get("offset_days", 0)
            time_str = timing_config.get("time", "09:00")  # HH:MM

            # Parsear hora
            hour, minute = map(int, time_str.split(":"))

            # Calcular fecha/hora
            target_date = reference_date + timedelta(days=offset_days)
            scheduled_time = datetime.combine(
                target_date.date(),
                dt_time(hour=hour, minute=minute),
            )

            return scheduled_time

        elif timing_type == "absolute":
            # Mismo día del evento, hora específica
            if not reference_date:
                raise ValueError("reference_date requerida para timing absoluto")

            time_str = timing_config.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))

            scheduled_time = datetime.combine(
                reference_date.date(),
                dt_time(hour=hour, minute=minute),
            )

            return scheduled_time

        else:
            raise ValueError(f"Tipo de timing desconocido: {timing_type}")

    async def schedule_notification(
        self,
        db: AsyncSession,
        company_id: UUID,
        template_id: UUID,
        recipients: List[Dict[str, Any]],
        message_context: Dict[str, Any],
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        reference_date: Optional[datetime] = None,
        custom_timing: Optional[Dict] = None,
    ) -> ScheduledNotification:
        """
        Programa una notificación para envío futuro.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            template_id: ID del template
            recipients: Lista de destinatarios [{"user_id": "...", "phone": "+56..."}, ...]
            message_context: Contexto para renderizar el mensaje
            entity_type: Tipo de entidad relacionada (opcional)
            entity_id: ID de la entidad (opcional)
            reference_date: Fecha de referencia para calcular timing
            custom_timing: Timing personalizado (sobrescribe el del template)

        Returns:
            ScheduledNotification creada
        """
        # Obtener template
        template = await self.get_template(db, template_id=template_id)
        if not template:
            raise ValueError(f"Template {template_id} no encontrado")

        # Verificar suscripción de la empresa
        subscription = await db.execute(
            select(NotificationSubscription).where(
                and_(
                    NotificationSubscription.company_id == company_id,
                    NotificationSubscription.notification_template_id == template_id,
                    NotificationSubscription.is_enabled == True,
                )
            )
        )
        subscription = subscription.scalar_one_or_none()

        # Usar timing custom de suscripción, parámetro, o template
        timing_config = (
            custom_timing
            or (subscription.custom_timing_config if subscription else None)
            or template.timing_config
        )

        # Calcular momento de envío
        scheduled_for = self._calculate_scheduled_time(timing_config, reference_date)

        # Si el tiempo ya pasó y es "immediate", enviar ahora
        if scheduled_for < datetime.utcnow():
            scheduled_for = datetime.utcnow()

        # Renderizar mensaje
        message_template = (
            (subscription.custom_message_template if subscription else None)
            or template.message_template
        )
        message_content = self._render_message(message_template, message_context)

        # Crear notificación programada
        scheduled = ScheduledNotification(
            company_id=company_id,
            notification_template_id=template_id,
            entity_type=entity_type,
            entity_id=entity_id,
            recipients=recipients,
            message_content=message_content,
            scheduled_for=scheduled_for,
            status="pending",
        )

        db.add(scheduled)
        await db.commit()
        await db.refresh(scheduled)

        logger.info(
            f"📅 Notificación programada: {template.name} para {len(recipients)} "
            f"destinatarios, envío: {scheduled_for}"
        )

        return scheduled

    # ========== Sending ==========

    async def get_pending_notifications(
        self,
        db: AsyncSession,
        limit: int = 50,
    ) -> List[ScheduledNotification]:
        """
        Obtiene notificaciones pendientes listas para enviar.

        Args:
            db: Sesión de base de datos
            limit: Límite de resultados

        Returns:
            Lista de notificaciones pendientes
        """
        now = datetime.utcnow()

        result = await db.execute(
            select(ScheduledNotification)
            .where(
                and_(
                    ScheduledNotification.status == "pending",
                    ScheduledNotification.scheduled_for <= now,
                    ScheduledNotification.send_attempts < 3,  # Máximo 3 intentos
                )
            )
            .order_by(ScheduledNotification.scheduled_for)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def _check_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        template: NotificationTemplate,
    ) -> bool:
        """
        Verifica si el usuario permite recibir esta notificación según sus preferencias.

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            company_id: ID de la empresa
            template: Template de la notificación

        Returns:
            True si debe enviarse, False si debe omitirse
        """
        # Obtener preferencias del usuario
        result = await db.execute(
            select(UserNotificationPreference).where(
                and_(
                    UserNotificationPreference.user_id == user_id,
                    UserNotificationPreference.company_id == company_id,
                )
            )
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            # Sin preferencias = enviar
            return True

        # Verificar si notificaciones están habilitadas
        if not prefs.notifications_enabled:
            logger.info(f"🔕 Usuario {user_id} tiene notificaciones deshabilitadas")
            return False

        # Verificar horarios de silencio
        now = datetime.utcnow()
        if prefs.quiet_hours_start and prefs.quiet_hours_end:
            current_time = now.time()
            if prefs.quiet_hours_start <= current_time <= prefs.quiet_hours_end:
                logger.info(f"🔕 Horario de silencio para usuario {user_id}")
                return False

        # Verificar días silenciados
        if prefs.quiet_days:
            weekday = now.strftime("%A").lower()
            if weekday in prefs.quiet_days:
                logger.info(f"🔕 Día silenciado para usuario {user_id}: {weekday}")
                return False

        # Verificar categorías silenciadas
        if prefs.muted_categories and template.category in prefs.muted_categories:
            logger.info(f"🔕 Categoría silenciada para usuario {user_id}: {template.category}")
            return False

        # Verificar templates silenciados
        if prefs.muted_templates and str(template.id) in prefs.muted_templates:
            logger.info(f"🔕 Template silenciado para usuario {user_id}")
            return False

        # TODO: Verificar límites de frecuencia (max_notifications_per_day, min_interval_minutes)

        return True

    async def send_scheduled_notification(
        self,
        db: AsyncSession,
        scheduled_id: UUID,
    ) -> Dict[str, Any]:
        """
        Envía una notificación programada.

        Args:
            db: Sesión de base de datos
            scheduled_id: ID de la notificación programada

        Returns:
            Resultado del envío con estadísticas
        """
        # Obtener notificación
        result = await db.execute(
            select(ScheduledNotification).where(ScheduledNotification.id == scheduled_id)
        )
        scheduled = result.scalar_one_or_none()

        if not scheduled:
            raise ValueError(f"Notificación {scheduled_id} no encontrada")

        if scheduled.status != "pending":
            raise ValueError(f"Notificación ya fue procesada: {scheduled.status}")

        # Marcar como en proceso
        scheduled.status = "processing"
        scheduled.last_attempt_at = datetime.utcnow()
        scheduled.send_attempts += 1
        await db.commit()

        # Obtener template
        template = await self.get_template(db, template_id=scheduled.notification_template_id)

        # Enviar a cada destinatario
        results = {
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "details": [],
        }

        for recipient in scheduled.recipients:
            user_id = recipient.get("user_id")
            phone = recipient.get("phone")

            if not phone:
                logger.warning(f"⚠️ Destinatario sin teléfono: {recipient}")
                results["skipped"] += 1
                continue

            # Verificar preferencias de usuario
            if user_id:
                should_send = await self._check_user_preferences(
                    db, UUID(user_id), scheduled.company_id, template
                )
                if not should_send:
                    results["skipped"] += 1
                    continue

            try:
                # Enviar por WhatsApp
                send_result = await self.whatsapp_service.send_text(
                    phone_number=phone,
                    message=scheduled.message_content,
                    whatsapp_config_id=None,  # Usará el default
                )

                # Registrar en historial
                history = NotificationHistory(
                    company_id=scheduled.company_id,
                    notification_template_id=scheduled.notification_template_id,
                    scheduled_notification_id=scheduled.id,
                    entity_type=scheduled.entity_type,
                    entity_id=scheduled.entity_id,
                    user_id=UUID(user_id) if user_id else None,
                    phone_number=phone,
                    message_content=scheduled.message_content,
                    status="sent",
                    whatsapp_conversation_id=send_result.get("conversation_id"),
                    whatsapp_message_id=send_result.get("message_id"),
                    sent_at=datetime.utcnow(),
                )
                db.add(history)

                results["sent"] += 1
                results["details"].append(
                    {
                        "phone": phone,
                        "status": "sent",
                        "message_id": send_result.get("message_id"),
                    }
                )

                logger.info(f"✅ Notificación enviada a {phone}")

            except Exception as e:
                logger.error(f"❌ Error enviando a {phone}: {e}")

                # Registrar error en historial
                history = NotificationHistory(
                    company_id=scheduled.company_id,
                    notification_template_id=scheduled.notification_template_id,
                    scheduled_notification_id=scheduled.id,
                    entity_type=scheduled.entity_type,
                    entity_id=scheduled.entity_id,
                    user_id=UUID(user_id) if user_id else None,
                    phone_number=phone,
                    message_content=scheduled.message_content,
                    status="failed",
                    error_message=str(e),
                    sent_at=datetime.utcnow(),
                )
                db.add(history)

                results["failed"] += 1
                results["details"].append({"phone": phone, "status": "failed", "error": str(e)})

        # Actualizar estado de la notificación programada
        if results["sent"] > 0:
            scheduled.status = "sent"
            scheduled.sent_at = datetime.utcnow()
            scheduled.send_results = results
        elif results["failed"] > 0 and results["sent"] == 0:
            scheduled.status = "failed"
            scheduled.error_message = f"Fallaron {results['failed']} envíos"
        else:
            scheduled.status = "skipped"

        await db.commit()

        logger.info(
            f"📊 Notificación {scheduled_id} procesada: "
            f"{results['sent']} enviadas, {results['failed']} fallidas, {results['skipped']} omitidas"
        )

        return results

    async def process_pending_notifications(
        self,
        db: AsyncSession,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Procesa un lote de notificaciones pendientes.
        Esta función debe ser llamada periódicamente (manual o por Celery).

        Args:
            db: Sesión de base de datos
            batch_size: Tamaño del lote a procesar

        Returns:
            Estadísticas del procesamiento
        """
        logger.info(f"🔄 Procesando notificaciones pendientes (batch: {batch_size})...")

        pending = await self.get_pending_notifications(db, limit=batch_size)

        stats = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0,
        }

        for notification in pending:
            try:
                result = await self.send_scheduled_notification(db, notification.id)
                stats["processed"] += 1
                stats["sent"] += result["sent"]
                stats["failed"] += result["failed"]
                stats["skipped"] += result["skipped"]
            except Exception as e:
                logger.error(f"❌ Error procesando notificación {notification.id}: {e}")
                stats["failed"] += 1

        logger.info(
            f"✅ Procesamiento completado: {stats['processed']} notificaciones, "
            f"{stats['sent']} mensajes enviados"
        )

        return stats

    # ========== History & Analytics ==========

    async def get_notification_history(
        self,
        db: AsyncSession,
        company_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[NotificationHistory]:
        """
        Obtiene el historial de notificaciones con filtros.

        Args:
            db: Sesión de base de datos
            company_id: Filtrar por empresa
            user_id: Filtrar por usuario
            entity_type: Filtrar por tipo de entidad
            entity_id: Filtrar por entidad específica
            status: Filtrar por estado
            limit: Límite de resultados

        Returns:
            Lista de registros de historial
        """
        query = select(NotificationHistory)

        if company_id:
            query = query.where(NotificationHistory.company_id == company_id)
        if user_id:
            query = query.where(NotificationHistory.user_id == user_id)
        if entity_type:
            query = query.where(NotificationHistory.entity_type == entity_type)
        if entity_id:
            query = query.where(NotificationHistory.entity_id == entity_id)
        if status:
            query = query.where(NotificationHistory.status == status)

        query = query.order_by(desc(NotificationHistory.sent_at)).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())
