"""
Business Summary Service Module

Servicio para generar resúmenes diarios de actividad empresarial.

Este módulo proporciona funcionalidad para:
- Analizar ventas y compras del día
- Contar nuevos proveedores
- Calcular variaciones respecto al día anterior
- Generar datos para notificaciones de resumen diario

Usage:
    from app.services.business_summary import get_business_summary_service

    async with AsyncSessionLocal() as db:
        service = await get_business_summary_service(db)
        summary = await service.get_daily_summary(company_id)
"""

from .service import BusinessSummaryService, get_business_summary_service

__all__ = [
    "BusinessSummaryService",
    "get_business_summary_service",
]
