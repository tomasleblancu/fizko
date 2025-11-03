"""
Event Config Service - Gestión de configuración de eventos (activar/desactivar)
"""
import logging
from typing import Dict, Any, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CompanyEvent
from .base_service import BaseCalendarService

logger = logging.getLogger(__name__)


class EventConfigService(BaseCalendarService):
    """
    Servicio para gestionar configuración de eventos de calendario

    Responsabilidades:
    - Activar eventos para empresas
    - Desactivar eventos de empresas
    - Actualizar configuraciones personalizadas
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio

        Args:
            db: Sesión de base de datos async
        """
        super().__init__(db)

    async def activate_event(
        self,
        company_id: Union[str, UUID],
        event_template_id: Union[str, UUID],
        custom_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Activa un tipo de evento tributario para una empresa.

        Crea o actualiza un CompanyEvent vinculando el evento a la empresa.

        Args:
            company_id: UUID de la empresa
            event_template_id: UUID del template de evento a activar
            custom_config: Configuración personalizada opcional

        Returns:
            Dict con información del evento activado

        Raises:
            ValueError: Si el event template no existe
        """
        company_id = self._convert_to_uuid(company_id)
        event_template_id = self._convert_to_uuid(event_template_id)

        logger.info(
            f"🔄 Activating event {event_template_id} for company {company_id}"
        )

        # Buscar si ya existe el vínculo empresa-evento
        company_event = await self._get_company_event(
            company_id=company_id,
            event_template_id=event_template_id,
            include_template=True
        )

        if company_event:
            # Actualizar vínculo existente
            action = await self._update_existing_company_event(
                company_event=company_event,
                custom_config=custom_config
            )
            event_template = company_event.event_template
        else:
            # Crear nuevo vínculo
            company_event, event_template, action = await self._create_new_company_event(
                company_id=company_id,
                event_template_id=event_template_id,
                custom_config=custom_config
            )

        # Commit de cambios
        await self.db.commit()

        logger.info(
            f"✅ Event '{event_template.name}' {action} for company {company_id}"
        )

        return {
            "success": True,
            "action": action,
            "company_event_id": str(company_event.id),
            "event_template_code": event_template.code,
            "event_template_name": event_template.name,
            "is_active": True,
            "custom_config": company_event.custom_config or {},
            "message": f"Evento '{event_template.name}' activado exitosamente"
        }

    async def deactivate_event(
        self,
        company_id: Union[str, UUID],
        event_template_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """
        Desactiva un tipo de evento tributario para una empresa.

        Marca el CompanyEvent como inactivo (no lo elimina para mantener historial).

        Args:
            company_id: UUID de la empresa
            event_template_id: UUID del template de evento a desactivar

        Returns:
            Dict con información del evento desactivado

        Raises:
            ValueError: Si el CompanyEvent no existe
        """
        company_id = self._convert_to_uuid(company_id)
        event_template_id = self._convert_to_uuid(event_template_id)

        logger.info(
            f"🔄 Deactivating event {event_template_id} for company {company_id}"
        )

        # Buscar el vínculo empresa-evento
        company_event = await self._get_company_event(
            company_id=company_id,
            event_template_id=event_template_id,
            include_template=True
        )

        if not company_event:
            raise ValueError(
                f"Company event not found for company {company_id} "
                f"and event template {event_template_id}"
            )

        # Desactivar el evento
        company_event.is_active = False

        # Commit de cambios
        await self.db.commit()

        logger.info(
            f"✅ Event '{company_event.event_template.name}' deactivated "
            f"for company {company_id}"
        )

        return {
            "success": True,
            "company_event_id": str(company_event.id),
            "event_template_code": company_event.event_template.code,
            "event_template_name": company_event.event_template.name,
            "is_active": False,
            "message": (
                f"Evento '{company_event.event_template.name}' "
                "desactivado exitosamente"
            )
        }

    async def _update_existing_company_event(
        self,
        company_event: CompanyEvent,
        custom_config: Dict[str, Any] = None
    ) -> str:
        """
        Actualiza un CompanyEvent existente

        Args:
            company_event: CompanyEvent a actualizar
            custom_config: Nueva configuración personalizada

        Returns:
            String indicando la acción ("updated")
        """
        company_event.is_active = True
        if custom_config:
            company_event.custom_config = custom_config

        logger.info(f"✅ Updated existing CompanyEvent {company_event.id}")
        return "updated"

    async def _create_new_company_event(
        self,
        company_id: UUID,
        event_template_id: UUID,
        custom_config: Dict[str, Any] = None
    ) -> tuple:
        """
        Crea un nuevo CompanyEvent

        Args:
            company_id: UUID de la empresa
            event_template_id: UUID del event template
            custom_config: Configuración personalizada

        Returns:
            Tupla (company_event, event_template, action)

        Raises:
            ValueError: Si el event template no existe
        """
        # Verificar que el event template existe
        event_template = await self._get_event_template(event_template_id)

        # Crear nuevo vínculo empresa-evento
        company_event = CompanyEvent(
            company_id=company_id,
            event_template_id=event_template_id,
            is_active=True,
            custom_config=custom_config or {}
        )
        self.db.add(company_event)

        logger.info(f"✅ Created new CompanyEvent for {event_template.code}")

        return company_event, event_template, "created"
