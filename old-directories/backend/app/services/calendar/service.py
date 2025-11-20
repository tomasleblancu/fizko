"""
Calendar Service - Servicio facade para operaciones de calendario

Este servicio actúa como punto de entrada unificado, delegando operaciones
a servicios especializados:
- EventConfigService: Activar/desactivar eventos
- SyncService: Sincronización de calendario
"""
import logging
from typing import Dict, Any, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .event_config_service import EventConfigService
from .sync_service import SyncService

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Servicio facade para operaciones de calendario tributario

    Proporciona una interfaz unificada para todas las operaciones de calendario,
    delegando a servicios especializados.

    Responsabilidades:
    - Punto de entrada unificado para operaciones de calendario
    - Delegación a servicios especializados
    - Gestión de sesión de base de datos compartida
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio facade

        Args:
            db: Sesión de base de datos async
        """
        self.db = db
        self._event_config_service = EventConfigService(db)
        self._sync_service = SyncService(db)

    # ==================== Event Config Operations ====================

    async def activate_event(
        self,
        company_id: Union[str, UUID],
        event_template_id: Union[str, UUID],
        custom_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Activa un tipo de evento tributario para una empresa.

        Delega a EventConfigService.

        Args:
            company_id: UUID de la empresa
            event_template_id: UUID del template de evento a activar
            custom_config: Configuración personalizada opcional

        Returns:
            Dict con información del evento activado

        Raises:
            ValueError: Si el event template no existe
        """
        return await self._event_config_service.activate_event(
            company_id=company_id,
            event_template_id=event_template_id,
            custom_config=custom_config
        )

    async def deactivate_event(
        self,
        company_id: Union[str, UUID],
        event_template_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """
        Desactiva un tipo de evento tributario para una empresa.

        Delega a EventConfigService.

        Args:
            company_id: UUID de la empresa
            event_template_id: UUID del template de evento a desactivar

        Returns:
            Dict con información del evento desactivado

        Raises:
            ValueError: Si el CompanyEvent no existe
        """
        return await self._event_config_service.deactivate_event(
            company_id=company_id,
            event_template_id=event_template_id
        )

    # ==================== Sync Operations ====================

    async def sync_company_calendar(
        self,
        company_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """
        Sincroniza el calendario de eventos tributarios para una empresa.

        Delega a SyncService.

        IMPORTANTE: Este método es idempotente. Puede ejecutarse múltiples veces
        sin duplicar eventos.

        Args:
            company_id: UUID de la empresa

        Returns:
            Dict con resumen de eventos creados y actualizados

        Raises:
            ValueError: Si la empresa no existe o no tiene eventos activos
        """
        return await self._sync_service.sync_company_calendar(
            company_id=company_id
        )


# Helper para dependency injection
async def get_calendar_service(db: AsyncSession) -> CalendarService:
    """Dependency injection para FastAPI"""
    return CalendarService(db)


# Helpers para acceso directo a servicios especializados (opcional)
async def get_event_config_service(db: AsyncSession) -> EventConfigService:
    """Dependency injection para EventConfigService directo"""
    return EventConfigService(db)


async def get_sync_service(db: AsyncSession) -> SyncService:
    """Dependency injection para SyncService directo"""
    return SyncService(db)
