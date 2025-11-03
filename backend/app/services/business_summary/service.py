"""
Business Summary Service

Servicio para generar resúmenes de actividad empresarial diaria.

Este servicio recopila estadísticas de:
- Ventas (documentos tributarios emitidos)
- Compras (documentos tributarios recibidos)
- Nuevos proveedores agregados
- Variación porcentual respecto al día anterior

Se utiliza para generar notificaciones de resumen diario.
"""
import logging
from datetime import date, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
import locale

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import (
    SalesDocumentRepository,
    PurchaseDocumentRepository,
    ContactRepository
)

logger = logging.getLogger(__name__)

# Nombres de los días en español
DAY_NAMES_ES = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}


def format_currency(amount: float) -> str:
    """
    Formatea un monto como moneda sin decimales y con separador de miles.

    Args:
        amount: Monto a formatear

    Returns:
        String formateado (ej: "1.234.567")

    Example:
        >>> format_currency(1234567.89)
        "1.234.567"
    """
    return f"{int(amount):,}".replace(",", ".")


class BusinessSummaryService:
    """
    Servicio para generar resúmenes de actividad empresarial.

    Este servicio analiza documentos tributarios y genera estadísticas
    agregadas para notificaciones de resumen diario.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            db: Sesión de base de datos async
        """
        self.db = db
        self.sales_repo = SalesDocumentRepository(db)
        self.purchases_repo = PurchaseDocumentRepository(db)
        self.contact_repo = ContactRepository(db)

    async def get_daily_summary(
        self,
        company_id: UUID,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene el resumen de actividad para una empresa en una fecha específica.

        Este método genera un resumen completo de la actividad empresarial
        del día, incluyendo ventas, compras, nuevos proveedores y variaciones.

        Args:
            company_id: ID de la empresa
            target_date: Fecha del resumen (por defecto: ayer)

        Returns:
            Diccionario con estadísticas del día:
            {
                "company_id": str,
                "date": str (ISO),
                "sales_count": int,
                "sales_total": float,
                "purchases_count": int,
                "purchases_total": float,
                "new_suppliers_count": int,
                "variation_percentage": float
            }

        Example:
            >>> summary = await service.get_daily_summary(company_id)
            >>> print(f"Ventas: {summary['sales_count']} por ${summary['sales_total']}")
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        logger.info(
            f"📊 Generating daily summary for company {company_id}, date {target_date}"
        )

        # 1. Ventas (Documentos emitidos)
        sales_stats = await self._get_sales_stats(company_id, target_date)

        # 2. Compras (Documentos recibidos)
        purchases_stats = await self._get_purchases_stats(company_id, target_date)

        # 3. Nuevos proveedores
        # TODO: Implementar cuando tengas el modelo de Supplier/Provider
        new_suppliers_count = await self._get_new_suppliers_count(company_id, target_date)

        # 4. Variación respecto al día anterior
        variation = await self._calculate_variation(company_id, target_date)

        # Obtener nombre del día en español
        day_name = DAY_NAMES_ES[target_date.weekday()]

        summary = {
            "company_id": str(company_id),
            "date": target_date.isoformat(),
            "day_name": day_name,
            "sales_count": sales_stats["count"],
            "sales_total": sales_stats["total"],
            "sales_total_formatted": format_currency(sales_stats["total"]),
            "purchases_count": purchases_stats["count"],
            "purchases_total": purchases_stats["total"],
            "purchases_total_formatted": format_currency(purchases_stats["total"]),
            "new_suppliers_count": new_suppliers_count,
            "variation_percentage": variation,
        }

        logger.info(
            f"✅ Summary generated for {target_date}: "
            f"{sales_stats['count']} sales (${sales_stats['total']}), "
            f"{purchases_stats['count']} purchases (${purchases_stats['total']})"
        )

        return summary

    async def get_weekly_summary(
        self,
        company_id: UUID,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene el resumen de actividad semanal para una empresa.

        Este método genera un resumen completo de la actividad empresarial
        de la última semana (últimos 7 días), incluyendo ventas, compras,
        nuevos proveedores y comparación con la semana anterior.

        Args:
            company_id: ID de la empresa
            target_date: Fecha de fin del período (por defecto: ayer)

        Returns:
            Diccionario con estadísticas semanales:
            {
                "company_id": str,
                "start_date": str (ISO),
                "end_date": str (ISO),
                "sales_count": int,
                "sales_total": float,
                "purchases_count": int,
                "purchases_total": float,
                "new_suppliers_count": int,
                "variation_percentage": float,
                "daily_breakdown": [...]  # Desglose diario
            }

        Example:
            >>> summary = await service.get_weekly_summary(company_id)
            >>> print(f"Ventas semanales: {summary['sales_count']} por ${summary['sales_total']}")
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        # Calcular fechas de la semana actual (últimos 7 días)
        end_date = target_date
        start_date = target_date - timedelta(days=6)

        logger.info(
            f"📊 Generating weekly summary for company {company_id}, "
            f"period {start_date} to {end_date}"
        )

        # 1. Estadísticas del período actual (7 días)
        current_sales = await self._get_sales_stats_range(company_id, start_date, end_date)
        current_purchases = await self._get_purchases_stats_range(company_id, start_date, end_date)
        new_suppliers = await self._get_new_suppliers_count_range(company_id, start_date, end_date)

        # 2. Estadísticas del período anterior (7 días previos)
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=6)
        previous_sales = await self._get_sales_stats_range(company_id, prev_start_date, prev_end_date)
        previous_purchases = await self._get_purchases_stats_range(company_id, prev_start_date, prev_end_date)

        # 3. Calcular variaciones semanales (ventas y compras por separado)
        if previous_sales["total"] == 0:
            sales_variation = 0.0 if current_sales["total"] == 0 else 100.0
        else:
            sales_variation = (
                (current_sales["total"] - previous_sales["total"])
                / previous_sales["total"]
                * 100
            )
            sales_variation = round(sales_variation, 2)

        if previous_purchases["total"] == 0:
            purchases_variation = 0.0 if current_purchases["total"] == 0 else 100.0
        else:
            purchases_variation = (
                (current_purchases["total"] - previous_purchases["total"])
                / previous_purchases["total"]
                * 100
            )
            purchases_variation = round(purchases_variation, 2)

        # 4. Desglose diario (últimos 7 días) y calcular día más activo
        daily_breakdown = []
        max_activity = 0
        most_active_day_date = start_date
        current_day = start_date
        while current_day <= end_date:
            day_sales = await self._get_sales_stats(company_id, current_day)
            day_purchases = await self._get_purchases_stats(company_id, current_day)
            daily_breakdown.append({
                "date": current_day.isoformat(),
                "sales_count": day_sales["count"],
                "sales_total": day_sales["total"],
                "purchases_count": day_purchases["count"],
                "purchases_total": day_purchases["total"],
            })
            # Calcular día más activo (por cantidad de documentos)
            daily_activity = day_sales["count"] + day_purchases["count"]
            if daily_activity > max_activity:
                max_activity = daily_activity
                most_active_day_date = current_day

            current_day += timedelta(days=1)

        # 5. Calcular ticket promedio de ventas
        avg_ticket_sale = current_sales["total"] / current_sales["count"] if current_sales["count"] > 0 else 0

        # 6. Obtener top customer y main supplier
        top_customer = await self._get_top_customer(company_id, start_date, end_date)
        main_supplier = await self._get_main_supplier(company_id, start_date, end_date)

        # 7. Nuevos clientes en la semana
        new_customers = await self._get_new_customers_count_range(company_id, start_date, end_date)

        # 8. Calcular número de semana
        week_number = end_date.isocalendar()[1]

        # 9. Nombre del día más activo
        most_active_day = DAY_NAMES_ES[most_active_day_date.weekday()]

        # 10. Total de documentos procesados
        total_documents = current_sales["count"] + current_purchases["count"]

        summary = {
            "company_id": str(company_id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "week_start_date": start_date.strftime("%d/%m/%Y"),
            "week_end_date": end_date.strftime("%d/%m/%Y"),
            "week_number": week_number,

            # Ventas
            "sales_count": current_sales["count"],
            "sales_count_week": current_sales["count"],
            "sales_total": current_sales["total"],
            "sales_total_week_formatted": format_currency(current_sales["total"]),
            "sales_variation_percent": sales_variation,
            "avg_ticket_sale": avg_ticket_sale,
            "avg_ticket_sale_formatted": format_currency(avg_ticket_sale),

            # Compras
            "purchases_count": current_purchases["count"],
            "purchases_count_week": current_purchases["count"],
            "purchases_total": current_purchases["total"],
            "purchases_total_week_formatted": format_currency(current_purchases["total"]),
            "purchases_variation_percent": purchases_variation,

            # Top customer
            "top_customer_name": top_customer["name"],
            "top_customer_total": top_customer["total"],
            "top_customer_total_formatted": format_currency(top_customer["total"]),

            # Main supplier
            "main_supplier_name": main_supplier["name"],
            "main_supplier_total": main_supplier["total"],
            "main_supplier_total_formatted": format_currency(main_supplier["total"]),

            # General
            "new_suppliers_count": new_suppliers,
            "new_customers_count": new_customers,
            "most_active_day": most_active_day,
            "total_documents_week": total_documents,

            # Legacy fields (mantener por compatibilidad)
            "variation_percentage": sales_variation,
            "daily_breakdown": daily_breakdown,
        }

        logger.info(
            f"✅ Weekly summary generated for {start_date} to {end_date}: "
            f"{current_sales['count']} sales (${current_sales['total']}), "
            f"{current_purchases['count']} purchases (${current_purchases['total']}), "
            f"sales_variation: {sales_variation}%, purchases_variation: {purchases_variation}%"
        )

        return summary

    async def _get_sales_stats(
        self,
        company_id: UUID,
        target_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de ventas (documentos emitidos).

        Cuenta y suma el total de documentos tributarios emitidos
        por la empresa en la fecha especificada.

        Args:
            company_id: ID de la empresa
            target_date: Fecha a consultar

        Returns:
            {"count": int, "total": float}
        """
        totals = await self.sales_repo.get_period_totals(
            company_id=company_id,
            start_date=target_date,
            end_date=target_date
        )

        return {
            "count": totals["document_count"],
            "total": totals["total_amount"]
        }

    async def _get_sales_stats_range(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de ventas en un rango de fechas.

        Args:
            company_id: ID de la empresa
            start_date: Fecha de inicio
            end_date: Fecha de fin

        Returns:
            {"count": int, "total": float}
        """
        totals = await self.sales_repo.get_period_totals(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "count": totals["document_count"],
            "total": totals["total_amount"]
        }

    async def _get_purchases_stats(
        self,
        company_id: UUID,
        target_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de compras (documentos recibidos).

        Cuenta y suma el total de documentos tributarios recibidos
        por la empresa en la fecha especificada.

        Args:
            company_id: ID de la empresa
            target_date: Fecha a consultar

        Returns:
            {"count": int, "total": float}
        """
        totals = await self.purchases_repo.get_period_totals(
            company_id=company_id,
            start_date=target_date,
            end_date=target_date
        )

        return {
            "count": totals["document_count"],
            "total": totals["total_amount"]
        }

    async def _get_purchases_stats_range(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de compras en un rango de fechas.

        Args:
            company_id: ID de la empresa
            start_date: Fecha de inicio
            end_date: Fecha de fin

        Returns:
            {"count": int, "total": float}
        """
        totals = await self.purchases_repo.get_period_totals(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "count": totals["document_count"],
            "total": totals["total_amount"]
        }

    async def _get_new_suppliers_count(
        self,
        company_id: UUID,
        target_date: date
    ) -> int:
        """
        Cuenta nuevos proveedores agregados en la fecha.

        TODO: Implementar cuando el modelo de Supplier/Provider esté disponible.

        Args:
            company_id: ID de la empresa
            target_date: Fecha a consultar

        Returns:
            Cantidad de nuevos proveedores (por ahora: 0)

        Example implementation:
            stmt = select(func.count(Supplier.id)).where(
                and_(
                    Supplier.company_id == company_id,
                    cast(Supplier.created_at, Date) == target_date
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
        """
        # Placeholder - retornar 0 hasta que se implemente el modelo
        logger.debug(
            f"⚠️  Supplier count not implemented yet - returning 0 for {target_date}"
        )
        return 0

    async def _get_new_suppliers_count_range(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> int:
        """
        Cuenta nuevos proveedores agregados en un rango de fechas.

        TODO: Implementar cuando el modelo de Supplier/Provider esté disponible.

        Args:
            company_id: ID de la empresa
            start_date: Fecha de inicio
            end_date: Fecha de fin

        Returns:
            Cantidad de nuevos proveedores (por ahora: 0)
        """
        # Placeholder - retornar 0 hasta que se implemente el modelo
        logger.debug(
            f"⚠️  Supplier count not implemented yet - returning 0 for range {start_date} to {end_date}"
        )
        return 0

    async def _calculate_variation(
        self,
        company_id: UUID,
        target_date: date
    ) -> float:
        """
        Calcula la variación de ventas respecto al día anterior.

        Calcula el cambio porcentual en el total de ventas comparando
        el día objetivo con el día anterior.

        Args:
            company_id: ID de la empresa
            target_date: Fecha a consultar

        Returns:
            Variación porcentual (ej: 12.5 para +12.5%, -5.2 para -5.2%)
            Si no hay ventas el día anterior, retorna 0.0

        Example:
            - Día anterior: $1000
            - Día actual: $1200
            - Variación: +20.0%
        """
        previous_date = target_date - timedelta(days=1)

        # Ventas del día objetivo
        current_sales = await self._get_sales_stats(company_id, target_date)

        # Ventas del día anterior
        previous_sales = await self._get_sales_stats(company_id, previous_date)

        if previous_sales["total"] == 0:
            # No hay ventas previas para comparar
            if current_sales["total"] > 0:
                logger.debug("No previous sales to compare - returning 0% variation")
            return 0.0

        # Calcular variación porcentual
        variation = (
            (current_sales["total"] - previous_sales["total"])
            / previous_sales["total"]
            * 100
        )

        return round(variation, 2)

    async def _get_top_customer(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene el cliente con mayor volumen de compras en el período.

        Usa ContactRepository para la consulta.

        Args:
            company_id: ID de la empresa
            start_date: Fecha de inicio
            end_date: Fecha de fin

        Returns:
            {"name": str, "total": float}
        """
        return await self.contact_repo.get_top_customer(company_id, start_date, end_date)

    async def _get_main_supplier(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene el proveedor con mayor volumen de ventas hacia la empresa en el período.

        Usa ContactRepository para la consulta.

        Args:
            company_id: ID de la empresa
            start_date: Fecha de inicio
            end_date: Fecha de fin

        Returns:
            {"name": str, "total": float}
        """
        return await self.contact_repo.get_main_supplier(company_id, start_date, end_date)

    async def _get_new_customers_count_range(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> int:
        """
        Cuenta nuevos clientes agregados en un rango de fechas.

        Un cliente se considera "nuevo" si su primer documento fue emitido en este período.
        Usa ContactRepository para la consulta.

        Args:
            company_id: ID de la empresa
            start_date: Fecha de inicio
            end_date: Fecha de fin

        Returns:
            Cantidad de nuevos clientes
        """
        return await self.contact_repo.get_new_customers_count(company_id, start_date, end_date)


async def get_business_summary_service(db: AsyncSession) -> BusinessSummaryService:
    """
    Factory function para obtener una instancia del servicio.

    Args:
        db: Sesión de base de datos async

    Returns:
        Instancia de BusinessSummaryService

    Example:
        >>> from app.config.database import AsyncSessionLocal
        >>> async with AsyncSessionLocal() as db:
        ...     service = await get_business_summary_service(db)
        ...     summary = await service.get_daily_summary(company_id)
    """
    return BusinessSummaryService(db)
