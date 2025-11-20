"""
Base service for calendar operations - Funcionalidad común
"""
import logging
from typing import Union, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Company, CompanyEvent, EventTemplate

logger = logging.getLogger(__name__)


class BaseCalendarService:
    """
    Servicio base para operaciones de calendario

    Proporciona funcionalidad común para todos los servicios de calendario:
    - Validación de empresas
    - Obtención de company_events
    - Helpers para conversión de tipos
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio base

        Args:
            db: Sesión de base de datos async
        """
        self.db = db

    def _convert_to_uuid(self, value: Union[str, UUID]) -> UUID:
        """
        Convierte un string o UUID a UUID

        Args:
            value: String o UUID a convertir

        Returns:
            UUID convertido
        """
        from uuid import UUID as UUIDType

        if isinstance(value, str):
            return UUIDType(value)
        return value

    async def _get_company(self, company_id: Union[str, UUID]) -> Company:
        """
        Obtiene una empresa por ID

        Args:
            company_id: UUID de la empresa

        Returns:
            Company encontrada

        Raises:
            ValueError: Si la empresa no existe
        """
        company_id = self._convert_to_uuid(company_id)

        company_stmt = select(Company).where(Company.id == company_id)
        company_result = await self.db.execute(company_stmt)
        company = company_result.scalar_one_or_none()

        if not company:
            raise ValueError(f"Company {company_id} not found")

        return company

    async def _get_event_template(
        self,
        event_template_id: Union[str, UUID]
    ) -> EventTemplate:
        """
        Obtiene un event template por ID

        Args:
            event_template_id: UUID del event template

        Returns:
            EventTemplate encontrado

        Raises:
            ValueError: Si el event template no existe
        """
        event_template_id = self._convert_to_uuid(event_template_id)

        event_template_stmt = select(EventTemplate).where(
            EventTemplate.id == event_template_id
        )
        event_template_result = await self.db.execute(event_template_stmt)
        event_template = event_template_result.scalar_one_or_none()

        if not event_template:
            raise ValueError(f"Event template {event_template_id} not found")

        return event_template

    async def _get_company_event(
        self,
        company_id: Union[str, UUID],
        event_template_id: Union[str, UUID],
        include_template: bool = True
    ) -> Optional[CompanyEvent]:
        """
        Obtiene un CompanyEvent por company_id y event_template_id

        Args:
            company_id: UUID de la empresa
            event_template_id: UUID del event template
            include_template: Si incluir el event_template en la query

        Returns:
            CompanyEvent si existe, None si no
        """
        from sqlalchemy.orm import selectinload

        company_id = self._convert_to_uuid(company_id)
        event_template_id = self._convert_to_uuid(event_template_id)

        stmt = select(CompanyEvent).where(
            CompanyEvent.company_id == company_id,
            CompanyEvent.event_template_id == event_template_id
        )

        if include_template:
            stmt = stmt.options(selectinload(CompanyEvent.event_template))

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
