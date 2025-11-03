"""
Contact Repository

Provides data access methods for Contact entities.
"""
import logging
from datetime import date
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Contact, PurchaseDocument, SalesDocument
from .base import BaseRepository

logger = logging.getLogger(__name__)


class ContactRepository(BaseRepository[Contact]):
    """Repository for Contact operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Contact, db)

    async def get_top_customer(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene el cliente con mayor volumen de compras en el período.

        Un cliente se define por documentos de venta emitidos (SalesDocument).

        Args:
            company_id: ID de la empresa
            start_date: Fecha de inicio del período
            end_date: Fecha de fin del período

        Returns:
            {"name": str, "total": float}
            Si no hay datos, retorna {"name": "Sin datos", "total": 0.0}
        """
        try:
            result = await self.db.execute(
                select(
                    Contact.business_name,
                    func.sum(SalesDocument.total_amount).label("total")
                )
                .join(SalesDocument, SalesDocument.contact_id == Contact.id)
                .where(
                    SalesDocument.company_id == company_id,
                    SalesDocument.issue_date >= start_date,
                    SalesDocument.issue_date <= end_date
                )
                .group_by(Contact.id, Contact.business_name)
                .order_by(desc("total"))
                .limit(1)
            )
            row = result.first()
            if row:
                return {
                    "name": row.business_name or "Cliente sin nombre",
                    "total": float(row.total)
                }
            return {"name": "Sin datos", "total": 0.0}
        except Exception as e:
            logger.error(f"Error getting top customer: {e}")
            return {"name": "Sin datos", "total": 0.0}

    async def get_main_supplier(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene el proveedor con mayor volumen de ventas hacia la empresa.

        Un proveedor se define por documentos de compra recibidos (PurchaseDocument).

        Args:
            company_id: ID de la empresa
            start_date: Fecha de inicio del período
            end_date: Fecha de fin del período

        Returns:
            {"name": str, "total": float}
            Si no hay datos, retorna {"name": "Sin datos", "total": 0.0}
        """
        try:
            result = await self.db.execute(
                select(
                    Contact.business_name,
                    func.sum(PurchaseDocument.total_amount).label("total")
                )
                .join(PurchaseDocument, PurchaseDocument.contact_id == Contact.id)
                .where(
                    PurchaseDocument.company_id == company_id,
                    PurchaseDocument.issue_date >= start_date,
                    PurchaseDocument.issue_date <= end_date
                )
                .group_by(Contact.id, Contact.business_name)
                .order_by(desc("total"))
                .limit(1)
            )
            row = result.first()
            if row:
                return {
                    "name": row.business_name or "Proveedor sin nombre",
                    "total": float(row.total)
                }
            return {"name": "Sin datos", "total": 0.0}
        except Exception as e:
            logger.error(f"Error getting main supplier: {e}")
            return {"name": "Sin datos", "total": 0.0}

    async def get_new_customers_count(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> int:
        """
        Cuenta nuevos clientes en un rango de fechas.

        Un cliente se considera "nuevo" si su primer documento de venta (SalesDocument)
        fue emitido dentro del período especificado.

        Args:
            company_id: ID de la empresa
            start_date: Fecha de inicio del período
            end_date: Fecha de fin del período

        Returns:
            Cantidad de nuevos clientes
        """
        try:
            # Subquery: primera fecha de documento por cliente
            first_doc_subq = (
                select(
                    SalesDocument.contact_id,
                    func.min(SalesDocument.issue_date).label("first_date")
                )
                .where(
                    SalesDocument.company_id == company_id,
                    SalesDocument.contact_id.isnot(None)
                )
                .group_by(SalesDocument.contact_id)
                .subquery()
            )

            # Query principal: contar contactos cuyo primer documento esté en rango
            result = await self.db.execute(
                select(func.count(first_doc_subq.c.contact_id))
                .where(
                    first_doc_subq.c.first_date >= start_date,
                    first_doc_subq.c.first_date <= end_date
                )
            )
            count = result.scalar()
            return count or 0
        except Exception as e:
            logger.error(f"Error getting new customers count: {e}")
            return 0

    async def find_by_company(
        self,
        company_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ):
        """
        Busca contactos de una empresa.

        Args:
            company_id: ID de la empresa
            limit: Límite de resultados (opcional)
            offset: Offset para paginación (opcional)

        Returns:
            Lista de contactos
        """
        query = select(Contact).where(Contact.company_id == company_id)

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()
