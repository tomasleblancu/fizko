"""
Sync Service - Sincronización de eventos de calendario
"""
import logging
from datetime import date, timedelta
from typing import Dict, Any, List, Union
from uuid import UUID
from dateutil.relativedelta import relativedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.db.models import CompanyEvent, CalendarEvent
from .base_service import BaseCalendarService

logger = logging.getLogger(__name__)


class SyncService(BaseCalendarService):
    """
    Servicio para sincronización de eventos de calendario

    Responsabilidades:
    - Sincronizar calendario completo de una empresa
    - Generar eventos mensuales y anuales
    - Actualizar estados de eventos
    - Gestionar eventos pendientes vs in_progress
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio

        Args:
            db: Sesión de base de datos async
        """
        super().__init__(db)

    async def sync_company_calendar(
        self,
        company_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """
        Sincroniza el calendario de eventos tributarios para una empresa.

        IMPORTANTE: Este método es idempotente. Puede ejecutarse múltiples veces
        sin duplicar eventos. Solo sincroniza eventos para los company_events
        activos (is_active=true).

        Flujo:
        1. Verifica que la empresa existe
        2. Obtiene los vínculos empresa-evento activos (company_events)
        3. Para cada tipo de evento (F29, F22, etc.):
           - Crea eventos faltantes para los próximos periodos
           - Actualiza el estado de eventos existentes
           - Solo el próximo a vencer queda con estado 'in_progress'
           - Los demás quedan con estado 'pending'
        4. No modifica eventos completados o cancelados

        Args:
            company_id: UUID de la empresa

        Returns:
            Dict con resumen de eventos creados y actualizados

        Raises:
            ValueError: Si la empresa no existe o no tiene eventos activos
        """
        company_id = self._convert_to_uuid(company_id)

        logger.info(f"🔄 Starting calendar sync for company {company_id}")

        # 1. Verificar que la empresa existe
        company = await self._get_company(company_id)
        logger.info(f"📅 Syncing calendar for company: {company.business_name}")

        # 2. Obtener SOLO los company_events activos
        active_company_events = await self._get_active_company_events(company_id)

        if not active_company_events:
            raise ValueError(
                "No hay eventos activos configurados para esta empresa. "
                "Primero activa eventos en /calendar-config/activate"
            )

        # 3. Generar eventos solo para los company_events activos
        created_events, updated_events = await self._sync_all_company_events(
            company_id=company_id,
            active_company_events=active_company_events
        )

        # 4. Commit de cambios
        await self.db.commit()

        logger.info(
            f"✅ Calendar sync completed for company {company_id}: "
            f"{len(active_company_events)} active company events, "
            f"{len(created_events)} created, {len(updated_events)} updated"
        )

        # Construir mensaje descriptivo
        message = self._build_sync_message(created_events, updated_events)

        return {
            "success": True,
            "company_id": str(company_id),
            "company_name": company.business_name,
            "active_company_events": [ce.event_template.code for ce in active_company_events],
            "created_events": created_events,
            "updated_events": updated_events,
            "total_created": len(created_events),
            "total_updated": len(updated_events),
            "message": message
        }

    async def _get_active_company_events(
        self,
        company_id: UUID
    ) -> List[CompanyEvent]:
        """
        Obtiene los CompanyEvents activos de una empresa

        Args:
            company_id: UUID de la empresa

        Returns:
            Lista de CompanyEvents activos
        """
        company_events_stmt = select(CompanyEvent).where(
            CompanyEvent.company_id == company_id,
            CompanyEvent.is_active == True
        ).options(selectinload(CompanyEvent.event_template))

        company_events_result = await self.db.execute(company_events_stmt)
        return list(company_events_result.scalars().all())

    async def _sync_all_company_events(
        self,
        company_id: UUID,
        active_company_events: List[CompanyEvent]
    ) -> tuple:
        """
        Sincroniza todos los CompanyEvents activos

        Args:
            company_id: UUID de la empresa
            active_company_events: Lista de CompanyEvents activos

        Returns:
            Tupla (created_events, updated_events)
        """
        created_events = []
        updated_events = []
        today = date.today()

        for company_event in active_company_events:
            event_template = company_event.event_template

            # Configuración del evento
            config = self._get_event_config(company_event)

            logger.info(
                f"🔄 Syncing events for {event_template.code} with config: {config}"
            )

            # Obtener eventos existentes
            existing_events = await self._get_existing_events(
                company_event_id=company_event.id,
                today=today
            )

            # Crear mapa de eventos existentes
            existing_events_map = {
                (event.due_date, event.period_start): event
                for event in existing_events
            }

            # Generar eventos según frecuencia
            events_to_create = self._generate_events_by_frequency(
                config=config,
                today=today,
                existing_events_map=existing_events_map
            )

            # Crear los eventos nuevos
            new_event_labels = await self._create_calendar_events(
                company_event=company_event,
                company_id=company_id,
                events_to_create=events_to_create,
                config=config
            )

            # Agregar labels de nuevos eventos al tracking
            for event_label in new_event_labels:
                created_events.append(event_label)

            # Actualizar estados de eventos existentes (no incluir los recién creados aún)
            updated = await self._update_event_statuses(
                existing_events=existing_events,
                event_template_code=event_template.code
            )
            updated_events.extend(updated)

        return created_events, updated_events

    def _get_event_config(self, company_event: CompanyEvent) -> Dict[str, Any]:
        """
        Obtiene la configuración de un evento (con overrides)

        Args:
            company_event: CompanyEvent con configuración

        Returns:
            Dict con configuración final
        """
        event_template = company_event.event_template
        config = {
            **event_template.default_recurrence,
            **company_event.custom_config.get('recurrence', {})
        } if company_event.custom_config else event_template.default_recurrence

        return config

    async def _get_existing_events(
        self,
        company_event_id: UUID,
        today: date
    ) -> List[CalendarEvent]:
        """
        Obtiene eventos existentes no completados/cancelados

        Args:
            company_event_id: UUID del CompanyEvent
            today: Fecha actual

        Returns:
            Lista de CalendarEvents existentes
        """
        existing_events_stmt = select(CalendarEvent).where(
            CalendarEvent.company_event_id == company_event_id,
            CalendarEvent.status.in_(['pending', 'in_progress', 'overdue']),
            CalendarEvent.due_date >= today
        ).order_by(CalendarEvent.due_date)

        existing_events_result = await self.db.execute(existing_events_stmt)
        return list(existing_events_result.scalars().all())

    def _generate_events_by_frequency(
        self,
        config: Dict[str, Any],
        today: date,
        existing_events_map: Dict[tuple, Any]
    ) -> List[Dict[str, Any]]:
        """
        Genera eventos según la frecuencia configurada

        Args:
            config: Configuración del evento
            today: Fecha actual
            existing_events_map: Mapa de eventos existentes

        Returns:
            Lista de datos de eventos a crear
        """
        if config['frequency'] == 'monthly':
            return self._generate_monthly_events(config, today, existing_events_map)
        elif config['frequency'] == 'annual':
            return self._generate_annual_events(config, today, existing_events_map)
        return []

    def _generate_monthly_events(
        self,
        config: Dict[str, Any],
        today: date,
        existing_events_map: Dict[tuple, Any]
    ) -> List[Dict[str, Any]]:
        """
        Genera eventos mensuales para los próximos 4 meses

        Args:
            config: Configuración de recurrencia del evento
            today: Fecha actual
            existing_events_map: Mapa de eventos existentes

        Returns:
            Lista de datos de eventos a crear
        """
        events_to_create = []

        for months_ahead in range(4):
            period_start = date(today.year, today.month, 1) + relativedelta(months=months_ahead)
            period_end = period_start + relativedelta(months=1) - timedelta(days=1)
            due_date = date(period_start.year, period_start.month, config['day_of_month'])

            # Si la fecha de vencimiento es anterior a hoy, saltear
            if due_date < today:
                continue

            # Si no existe, agregarlo a la lista para crear
            if (due_date, period_start) not in existing_events_map:
                events_to_create.append({
                    'due_date': due_date,
                    'period_start': period_start,
                    'period_end': period_end
                })

        return events_to_create

    def _generate_annual_events(
        self,
        config: Dict[str, Any],
        today: date,
        existing_events_map: Dict[tuple, Any]
    ) -> List[Dict[str, Any]]:
        """
        Genera eventos anuales para el próximo año si aún no pasó

        Args:
            config: Configuración de recurrencia del evento
            today: Fecha actual
            existing_events_map: Mapa de eventos existentes

        Returns:
            Lista de datos de eventos a crear
        """
        events_to_create = []
        year = today.year

        # Soportar tanto 'month_of_year' como 'months' (lista)
        month = (
            config.get('month_of_year') or
            (config.get('months', [1])[0] if config.get('months') else 1)
        )

        if today.month >= month:
            year += 1

        period_start = date(year - 1, 1, 1)
        period_end = date(year - 1, 12, 31)
        due_date = date(year, month, config['day_of_month'])

        if due_date >= today:
            # Si no existe, agregarlo a la lista para crear
            if (due_date, period_start) not in existing_events_map:
                events_to_create.append({
                    'due_date': due_date,
                    'period_start': period_start,
                    'period_end': period_end
                })

        return events_to_create

    async def _create_calendar_events(
        self,
        company_event: CompanyEvent,
        company_id: UUID,
        events_to_create: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Crea CalendarEvents en la base de datos

        Args:
            company_event: CompanyEvent padre
            company_id: UUID de la empresa
            events_to_create: Lista de datos de eventos
            config: Configuración del evento

        Returns:
            Lista de labels de eventos creados
        """
        created_labels = []
        event_template = company_event.event_template

        for event_data in events_to_create:
            event = CalendarEvent(
                company_event_id=company_event.id,
                company_id=company_id,
                event_template_id=event_template.id,
                due_date=event_data['due_date'],
                period_start=event_data['period_start'],
                period_end=event_data['period_end'],
                status='pending',  # Se creará como pending
                auto_generated=True
            )
            self.db.add(event)

            # Log para tracking
            period_label = (
                event_data['period_start'].strftime('%Y-%m')
                if config['frequency'] == 'monthly'
                else f"AT{event_data['period_start'].year}"
            )
            created_labels.append(f"{event_template.code}:{period_label}")
            logger.debug(f"  ✅ Created event: {event_template.code} for {period_label}")

        return created_labels

    async def _update_event_statuses(
        self,
        existing_events: List[CalendarEvent],
        event_template_code: str
    ) -> List[str]:
        """
        Actualiza estados de eventos (solo el primero en 'in_progress')

        Args:
            existing_events: Lista de CalendarEvents existentes
            event_template_code: Código del event template

        Returns:
            Lista de labels de eventos actualizados
        """
        updated_labels = []

        # Ordenar por fecha de vencimiento
        existing_events.sort(key=lambda e: e.due_date)

        for idx, event in enumerate(existing_events):
            expected_status = 'in_progress' if idx == 0 else 'saved'

            # Solo actualizar si cambió el estado
            if (event.status != expected_status and
                event.status in ['saved', 'in_progress', 'overdue']):
                event.status = expected_status
                period_label = (
                    event.period_start.strftime('%Y-%m')
                    if event.period_start
                    else 'N/A'
                )
                updated_labels.append(f"{event_template_code}:{period_label}")

        return updated_labels

    def _build_sync_message(
        self,
        created_events: List[str],
        updated_events: List[str]
    ) -> str:
        """
        Construye mensaje descriptivo de sincronización

        Args:
            created_events: Lista de eventos creados
            updated_events: Lista de eventos actualizados

        Returns:
            Mensaje descriptivo
        """
        messages = []
        if created_events:
            messages.append(f"{len(created_events)} eventos creados")
        if updated_events:
            messages.append(f"{len(updated_events)} eventos actualizados")

        return (
            "Calendario sincronizado: " + ", ".join(messages)
            if messages
            else "Calendario sincronizado: sin cambios"
        )
