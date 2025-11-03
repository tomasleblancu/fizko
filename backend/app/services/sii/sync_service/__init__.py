"""
Servicio de sincronización de documentos tributarios SII

Este módulo coordina la extracción y persistencia de documentos tributarios
desde el SII hacia la base de datos de la aplicación.

Arquitectura modular:
- parsers.py: Funciones de parseo y mapeo de documentos
- persistence.py: Funciones de guardado y actualización en DB
- compras_sync.py: Lógica específica de sincronización de compras
- ventas_sync.py: Lógica específica de sincronización de ventas
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.sii.service import SIIService
from app.db.models import Session as SessionModel
from .compras_sync import sync_compras_period
from .ventas_sync import sync_ventas_period
from .honorarios_sync import sync_honorarios_period

logger = logging.getLogger(__name__)


class SIISyncService:
    """
    Servicio orquestador de sincronización de documentos tributarios

    Responsabilidades:
    1. Calcular períodos a sincronizar (últimos N meses)
    2. Coordinar sincronización de compras, ventas y boletas de honorarios por período
    3. Trackear progreso (nuevos, actualizados, errores)
    4. Logging detallado del proceso

    Delega la lógica específica de compras, ventas y boletas a módulos separados.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio de sincronización

        Args:
            db: Sesión de base de datos async
        """
        self.db = db
        self.sii_service = SIIService(db)

    async def sync_last_n_months(
        self,
        session_id: UUID,
        months: int = 3
    ) -> Dict[str, Any]:
        """
        Sincroniza documentos tributarios de los últimos N meses

        Args:
            session_id: ID de sesión con credenciales SII
            months: Cantidad de meses a sincronizar (default: 3)

        Returns:
            Dict con resumen de sincronización:
            {
                "compras": {"total": int, "nuevos": int, "actualizados": int},
                "ventas": {"total": int, "nuevos": int, "actualizados": int},
                "periods_processed": List[str],
                "errors": List[Dict],
                "duration_seconds": float
            }

        Raises:
            ValueError: Si la sesión no existe
        """
        start_time = datetime.now()

        logger.info(f"🚀 Starting sync for session {session_id} - last {months} months")

        # Obtener company_id de la sesión
        company_id = await self._get_company_id_from_session(session_id)

        # Calcular períodos a sincronizar
        periods = self._calculate_periods(months)
        logger.info(f"📅 Periods to sync: {periods}")

        # Resultado acumulado
        results = {
            "compras": {"total": 0, "nuevos": 0, "actualizados": 0},
            "ventas": {"total": 0, "nuevos": 0, "actualizados": 0},
            "honorarios": {"total": 0, "nuevos": 0, "actualizados": 0},
            "periods_processed": [],
            "errors": []
        }

        # Sincronizar cada período
        for period in periods:
            logger.info(f"📄 Processing period: {period}")

            # Sincronizar compras del período
            compras_result = {"total": 0, "nuevos": 0, "actualizados": 0}
            try:
                compras_result = await sync_compras_period(
                    db=self.db,
                    sii_service=self.sii_service,
                    session_id=session_id,
                    company_id=company_id,
                    period=period
                )
                results["compras"]["total"] += compras_result["total"]
                results["compras"]["nuevos"] += compras_result["nuevos"]
                results["compras"]["actualizados"] += compras_result["actualizados"]
            except Exception as e:
                error_msg = f"Error processing compras for period {period}"
                logger.error(
                    f"❌ {error_msg}",
                    exc_info=True,
                    extra={
                        "session_id": str(session_id),
                        "company_id": str(company_id),
                        "period": period,
                        "document_type": "compras",
                        "error_type": type(e).__name__
                    }
                )
                results["errors"].append({
                    "period": period,
                    "type": "compras",
                    "error": str(e),
                    "exception_type": type(e).__name__
                })

            # Sincronizar ventas del período (independiente de si compras falló)
            ventas_result = {"total": 0, "nuevos": 0, "actualizados": 0}
            try:
                ventas_result = await sync_ventas_period(
                    db=self.db,
                    sii_service=self.sii_service,
                    session_id=session_id,
                    company_id=company_id,
                    period=period
                )
                results["ventas"]["total"] += ventas_result["total"]
                results["ventas"]["nuevos"] += ventas_result["nuevos"]
                results["ventas"]["actualizados"] += ventas_result["actualizados"]
            except Exception as e:
                error_msg = f"Error processing ventas for period {period}"
                logger.error(
                    f"❌ {error_msg}",
                    exc_info=True,
                    extra={
                        "session_id": str(session_id),
                        "company_id": str(company_id),
                        "period": period,
                        "document_type": "ventas",
                        "error_type": type(e).__name__
                    }
                )
                results["errors"].append({
                    "period": period,
                    "type": "ventas",
                    "error": str(e),
                    "exception_type": type(e).__name__
                })

            # Sincronizar boletas de honorarios del período (independiente de los anteriores)
            honorarios_result = {"total": 0, "nuevos": 0, "actualizados": 0}
            try:
                honorarios_result = await sync_honorarios_period(
                    db=self.db,
                    sii_service=self.sii_service,
                    session_id=session_id,
                    company_id=company_id,
                    period=period
                )
                results["honorarios"]["total"] += honorarios_result["total"]
                results["honorarios"]["nuevos"] += honorarios_result["nuevos"]
                results["honorarios"]["actualizados"] += honorarios_result["actualizados"]
            except Exception as e:
                error_msg = f"Error processing honorarios for period {period}"
                logger.error(
                    f"❌ {error_msg}",
                    exc_info=True,
                    extra={
                        "session_id": str(session_id),
                        "company_id": str(company_id),
                        "period": period,
                        "document_type": "honorarios",
                        "error_type": type(e).__name__
                    }
                )
                results["errors"].append({
                    "period": period,
                    "type": "honorarios",
                    "error": str(e),
                    "exception_type": type(e).__name__
                })

            # Marcar período como procesado (aunque haya errores parciales)
            results["periods_processed"].append(period)

            logger.info(
                f"✅ Period {period} completed: "
                f"Compras ({compras_result['nuevos']} nuevos, {compras_result['actualizados']} actualizados), "
                f"Ventas ({ventas_result['nuevos']} nuevos, {ventas_result['actualizados']} actualizados), "
                f"Honorarios ({honorarios_result['nuevos']} nuevos, {honorarios_result['actualizados']} actualizados)"
            )

        # Calcular duración
        duration = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = duration

        logger.info(
            f"🎉 Sync completed in {duration:.2f}s: "
            f"Compras: {results['compras']}, Ventas: {results['ventas']}, "
            f"Honorarios: {results['honorarios']}, "
            f"Errors: {len(results['errors'])}"
        )

        return results

    async def sync_compras_period(
        self,
        session_id: UUID,
        company_id: UUID,
        year: int,
        month: int
    ) -> Dict[str, int]:
        """
        Sincroniza compras de un período específico (método público para routers)

        Args:
            session_id: ID de sesión con credenciales SII
            company_id: ID de la compañía
            year: Año del período
            month: Mes del período

        Returns:
            {"total": int, "nuevos": int, "actualizados": int}
        """
        # Convertir year/month a formato YYYYMM
        period = f"{year}{month:02d}"

        return await sync_compras_period(
            db=self.db,
            sii_service=self.sii_service,
            session_id=session_id,
            company_id=company_id,
            period=period
        )

    async def sync_ventas_period(
        self,
        session_id: UUID,
        company_id: UUID,
        year: int,
        month: int
    ) -> Dict[str, int]:
        """
        Sincroniza ventas de un período específico (método público para routers)

        Args:
            session_id: ID de sesión con credenciales SII
            company_id: ID de la compañía
            year: Año del período
            month: Mes del período

        Returns:
            {"total": int, "nuevos": int, "actualizados": int}
        """
        # Convertir year/month a formato YYYYMM
        period = f"{year}{month:02d}"

        return await sync_ventas_period(
            db=self.db,
            sii_service=self.sii_service,
            session_id=session_id,
            company_id=company_id,
            period=period
        )

    async def _get_company_id_from_session(self, session_id: UUID) -> UUID:
        """Obtiene el company_id de una sesión"""
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        return session.company_id

    def _calculate_periods(self, months: int) -> List[str]:
        """
        Calcula los períodos en formato YYYYMM

        Args:
            months: Cantidad de meses hacia atrás

        Returns:
            Lista de períodos en formato YYYYMM, ordenados descendente

        Example:
            Si hoy es 2024-03-15 y months=3:
            ['202403', '202402', '202401']
        """
        periods = []
        now = datetime.now()

        for i in range(months):
            # Retroceder i meses
            target_date = now - timedelta(days=30 * i)
            period = target_date.strftime("%Y%m")

            # Evitar duplicados (puede pasar si el mes tiene 31 días)
            if period not in periods:
                periods.append(period)

        return periods


# Dependency injection para FastAPI
async def get_sii_sync_service(db: AsyncSession) -> SIISyncService:
    """Factory para crear instancia de SIISyncService"""
    return SIISyncService(db)


# Re-exportar para compatibilidad con imports existentes
__all__ = ['SIISyncService', 'get_sii_sync_service']
