"""
Base Service para integración SII
Proporciona funcionalidad común de autenticación, sesiones y cookies
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, update

from app.db.models import Session as SessionModel
from app.config.database import SyncSessionLocal

logger = logging.getLogger(__name__)


class BaseSIIService:
    """
    Servicio base para integración SII.

    Proporciona funcionalidad común:
    - Gestión de credenciales
    - Gestión de cookies
    - Gestión de sesiones

    Todos los servicios SII deben heredar de esta clase.
    """

    def __init__(self, db: Union[AsyncSession, Session]):
        """
        Inicializa el servicio base

        Args:
            db: Sesión de base de datos (async o sync)
        """
        self.db = db
        self.is_async = isinstance(db, AsyncSession)

    # =============================================================================
    # GESTIÓN DE CREDENCIALES
    # =============================================================================

    def _get_stored_credentials_sync(
        self,
        session_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene las credenciales almacenadas en la DB (versión SÍNCRONA)

        Usa una sesión sync separada para evitar conflictos con Selenium.

        Args:
            session_id: ID de la sesión en la DB (puede ser str o UUID)

        Returns:
            Dict con rut, password, cookies y company_id (si existen)
        """
        from uuid import UUID as UUIDType

        # Convertir a UUID si es string
        if isinstance(session_id, str):
            session_id = UUIDType(session_id)

        # Usar una sesión sync separada
        with SyncSessionLocal() as sync_db:
            stmt = select(SessionModel).where(SessionModel.id == session_id)
            result = sync_db.execute(stmt)
            session = result.scalar_one_or_none()

            if not session:
                return None

            return {
                "rut": session.company.rut,
                "password": session.company.sii_password,
                "cookies": session.cookies.get("sii_cookies") if session.cookies else None,
                "session_db_id": session.id,
                "company_id": session.company_id
            }

    async def get_stored_credentials(
        self,
        session_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene las credenciales almacenadas en la DB (versión ASYNC)

        Args:
            session_id: ID de la sesión en la DB

        Returns:
            Dict con rut, password, cookies y company_id (si existen)
        """
        from uuid import UUID as UUIDType

        # Convertir a UUID si es string
        if isinstance(session_id, str):
            session_id = UUIDType(session_id)

        stmt = select(SessionModel).where(SessionModel.id == session_id).options(
            selectinload(SessionModel.company)
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        return {
            "rut": session.company.rut,
            "password": session.company.sii_password,
            "cookies": session.cookies.get("sii_cookies") if session.cookies else None,
            "session_db_id": session.id,
            "company_id": session.company_id
        }

    # =============================================================================
    # GESTIÓN DE COOKIES
    # =============================================================================

    def _save_cookies_sync(
        self,
        session_id: Union[str, UUID],
        cookies: List[Dict]
    ) -> None:
        """
        Guarda las cookies en la DB para reutilización futura (versión SÍNCRONA)

        Args:
            session_id: ID de la sesión en la DB (puede ser str o UUID)
            cookies: Lista de cookies del SII
        """
        from uuid import UUID as UUIDType

        # Convertir a UUID si es string
        if isinstance(session_id, str):
            session_id = UUIDType(session_id)

        with SyncSessionLocal() as sync_db:
            stmt = (
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(
                    cookies={
                        "sii_cookies": cookies,
                        "updated_at": datetime.utcnow().isoformat()
                    },
                    last_accessed_at=datetime.utcnow()
                )
            )
            sync_db.execute(stmt)
            sync_db.commit()

            logger.debug(f"✅ Saved {len(cookies)} cookies to DB for session {session_id}")

    async def save_cookies(
        self,
        session_id: Union[str, UUID],
        cookies: List[Dict]
    ) -> None:
        """
        Guarda las cookies en la DB para reutilización futura (versión ASYNC)

        Args:
            session_id: ID de la sesión en la DB
            cookies: Lista de cookies del SII
        """
        from uuid import UUID as UUIDType

        # Convertir a UUID si es string
        if isinstance(session_id, str):
            session_id = UUIDType(session_id)

        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                cookies={
                    "sii_cookies": cookies,
                    "updated_at": datetime.utcnow().isoformat()
                },
                last_accessed_at=datetime.utcnow()
            )
        )
        await self.db.execute(stmt)
        # No commit aquí - se hace en el caller
        # await self.db.commit()

        logger.debug(f"✅ Saved {len(cookies)} cookies to DB for session {session_id}")

    # =============================================================================
    # HELPERS DE SESIÓN
    # =============================================================================

    async def get_company_id_from_session(
        self,
        session_id: Union[str, UUID]
    ) -> Optional[UUID]:
        """
        Obtiene el company_id desde una sesión

        Args:
            session_id: UUID de la sesión

        Returns:
            UUID del company o None si no existe la sesión
        """
        from uuid import UUID as UUIDType

        # Convertir a UUID si es string
        if isinstance(session_id, str):
            session_id = UUIDType(session_id)

        session_result = await self.db.execute(
            select(SessionModel.company_id).where(SessionModel.id == session_id)
        )
        company_id_row = session_result.first()

        if not company_id_row:
            return None

        return company_id_row[0]
