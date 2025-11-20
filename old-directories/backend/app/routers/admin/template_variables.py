"""
Template Variables API

Endpoint para obtener las variables disponibles para cada tipo de template.
Las variables se obtienen dinámicamente analizando los métodos del BusinessSummaryService.
"""
import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.services.business_summary import get_business_summary_service
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/template-variables", tags=["template-variables"])


# Metadata de variables por service_method
# Estas son las variables que devuelve cada método del BusinessSummaryService
SERVICE_METHOD_VARIABLES: Dict[str, Dict[str, Any]] = {
    "get_daily_summary": {
        "name": "Resumen Diario de Negocio",
        "description": "Variables disponibles para el resumen diario de actividad empresarial",
        "method": "get_daily_summary",
        "service": "BusinessSummaryService",
        "variables": [
            {
                "name": "company_id",
                "type": "string",
                "description": "UUID de la empresa",
                "example": "123e4567-e89b-12d3-a456-426614174000"
            },
            {
                "name": "date",
                "type": "string",
                "description": "Fecha del resumen (formato ISO: YYYY-MM-DD)",
                "example": "2025-11-02"
            },
            {
                "name": "day_name",
                "type": "string",
                "description": "Nombre del día en español (Lunes, Martes, etc.)",
                "example": "Sábado"
            },
            {
                "name": "sales_count",
                "type": "integer",
                "description": "Cantidad de documentos de venta emitidos",
                "example": "15"
            },
            {
                "name": "sales_total",
                "type": "float",
                "description": "Monto total de ventas en pesos (número sin formato)",
                "example": "2500000.50"
            },
            {
                "name": "sales_total_formatted",
                "type": "string",
                "description": "Monto total de ventas formateado sin decimales y con separador de miles",
                "example": "2.500.000"
            },
            {
                "name": "purchases_count",
                "type": "integer",
                "description": "Cantidad de documentos de compra recibidos",
                "example": "8"
            },
            {
                "name": "purchases_total",
                "type": "float",
                "description": "Monto total de compras en pesos (número sin formato)",
                "example": "1200000.00"
            },
            {
                "name": "purchases_total_formatted",
                "type": "string",
                "description": "Monto total de compras formateado sin decimales y con separador de miles",
                "example": "1.200.000"
            },
            {
                "name": "new_suppliers_count",
                "type": "integer",
                "description": "Nuevos proveedores agregados (actualmente siempre 0)",
                "example": "0"
            },
            {
                "name": "variation_percentage",
                "type": "float",
                "description": "Variación porcentual respecto al día anterior (+/- %)",
                "example": "12.5"
            },
        ]
    },
    "get_weekly_summary": {
        "name": "Resumen Semanal de Negocio",
        "description": "Variables disponibles para el resumen semanal de actividad empresarial",
        "method": "get_weekly_summary",
        "service": "BusinessSummaryService",
        "variables": [
            {
                "name": "company_id",
                "type": "string",
                "description": "UUID de la empresa",
                "example": "123e4567-e89b-12d3-a456-426614174000"
            },
            {
                "name": "week_number",
                "type": "integer",
                "description": "Número de semana del año (1-52)",
                "example": "44"
            },
            {
                "name": "start_date",
                "type": "string",
                "description": "Fecha de inicio del período (formato ISO: YYYY-MM-DD)",
                "example": "2025-10-27"
            },
            {
                "name": "end_date",
                "type": "string",
                "description": "Fecha de fin del período (formato ISO: YYYY-MM-DD)",
                "example": "2025-11-02"
            },
            {
                "name": "week_start_date",
                "type": "string",
                "description": "Fecha de inicio formateada (DD/MM/YYYY)",
                "example": "27/10/2025"
            },
            {
                "name": "week_end_date",
                "type": "string",
                "description": "Fecha de fin formateada (DD/MM/YYYY)",
                "example": "02/11/2025"
            },
            # Ventas
            {
                "name": "sales_count",
                "type": "integer",
                "description": "Cantidad total de documentos de venta del período",
                "example": "95"
            },
            {
                "name": "sales_count_week",
                "type": "integer",
                "description": "Alias de sales_count para claridad en templates",
                "example": "95"
            },
            {
                "name": "sales_total",
                "type": "float",
                "description": "Monto total de ventas del período en pesos",
                "example": "15750000.00"
            },
            {
                "name": "sales_total_week_formatted",
                "type": "string",
                "description": "Monto total de ventas formateado sin decimales y con separador de miles",
                "example": "15.750.000"
            },
            {
                "name": "sales_variation_percent",
                "type": "float",
                "description": "Variación porcentual de ventas respecto a la semana anterior (+/- %)",
                "example": "8.3"
            },
            {
                "name": "avg_ticket_sale",
                "type": "float",
                "description": "Ticket promedio de venta (total/cantidad)",
                "example": "165789.47"
            },
            {
                "name": "avg_ticket_sale_formatted",
                "type": "string",
                "description": "Ticket promedio formateado sin decimales",
                "example": "165.789"
            },
            # Top customer
            {
                "name": "top_customer_name",
                "type": "string",
                "description": "Nombre del cliente con mayor volumen de compras",
                "example": "Empresa ABC Ltda."
            },
            {
                "name": "top_customer_total",
                "type": "float",
                "description": "Monto total del top customer",
                "example": "3500000.00"
            },
            {
                "name": "top_customer_total_formatted",
                "type": "string",
                "description": "Monto del top customer formateado",
                "example": "3.500.000"
            },
            # Compras
            {
                "name": "purchases_count",
                "type": "integer",
                "description": "Cantidad total de documentos de compra del período",
                "example": "52"
            },
            {
                "name": "purchases_count_week",
                "type": "integer",
                "description": "Alias de purchases_count para claridad en templates",
                "example": "52"
            },
            {
                "name": "purchases_total",
                "type": "float",
                "description": "Monto total de compras del período en pesos",
                "example": "8900000.00"
            },
            {
                "name": "purchases_total_week_formatted",
                "type": "string",
                "description": "Monto total de compras formateado sin decimales y con separador de miles",
                "example": "8.900.000"
            },
            {
                "name": "purchases_variation_percent",
                "type": "float",
                "description": "Variación porcentual de compras respecto a la semana anterior (+/- %)",
                "example": "5.2"
            },
            # Main supplier
            {
                "name": "main_supplier_name",
                "type": "string",
                "description": "Nombre del proveedor con mayor volumen de ventas",
                "example": "Distribuidora XYZ S.A."
            },
            {
                "name": "main_supplier_total",
                "type": "float",
                "description": "Monto total del proveedor principal",
                "example": "2100000.00"
            },
            {
                "name": "main_supplier_total_formatted",
                "type": "string",
                "description": "Monto del proveedor principal formateado",
                "example": "2.100.000"
            },
            # General
            {
                "name": "new_suppliers_count",
                "type": "integer",
                "description": "Nuevos proveedores agregados en el período",
                "example": "0"
            },
            {
                "name": "new_customers_count",
                "type": "integer",
                "description": "Nuevos clientes en la semana (primer documento emitido)",
                "example": "7"
            },
            {
                "name": "most_active_day",
                "type": "string",
                "description": "Día de la semana con mayor actividad (nombre en español)",
                "example": "Miércoles"
            },
            {
                "name": "total_documents_week",
                "type": "integer",
                "description": "Total de documentos procesados (ventas + compras)",
                "example": "147"
            },
            # Legacy (mantener por compatibilidad)
            {
                "name": "variation_percentage",
                "type": "float",
                "description": "Alias de sales_variation_percent (legacy)",
                "example": "8.3"
            },
        ]
    },
    "calendar_event": {
        "name": "Evento de Calendario",
        "description": "Variables disponibles para notificaciones de eventos de calendario",
        "method": "calendar_event",
        "service": "CalendarService",
        "variables": [
            {
                "name": "event_title",
                "type": "string",
                "description": "Título del evento",
                "example": "Declaración IVA"
            },
            {
                "name": "due_date",
                "type": "string",
                "description": "Fecha de vencimiento del evento",
                "example": "2025-11-15"
            },
            {
                "name": "event_type",
                "type": "string",
                "description": "Tipo de evento (tax_deadline, payroll_deadline, etc.)",
                "example": "tax_deadline"
            },
            {
                "name": "event_description",
                "type": "string",
                "description": "Descripción del evento",
                "example": "Declaración mensual de IVA"
            },
        ]
    }
}


@router.get("")
async def get_all_template_variables(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Obtiene todas las variables disponibles para todos los service methods.

    Returns:
        Diccionario con metadata de variables para cada service method
    """
    return {
        "success": True,
        "data": SERVICE_METHOD_VARIABLES
    }


@router.get("/by-method/{service_method}")
async def get_variables_by_service_method(
    service_method: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Obtiene las variables disponibles para un service_method específico.

    Args:
        service_method: Nombre del método del servicio (ej: get_daily_summary)

    Returns:
        Metadata de variables para el service method específico
    """
    if service_method not in SERVICE_METHOD_VARIABLES:
        return {
            "success": False,
            "error": f"No se encontraron variables para el método '{service_method}'",
            "data": {
                "name": "Método Personalizado",
                "description": "No hay variables predefinidas para este método",
                "variables": []
            }
        }

    return {
        "success": True,
        "data": SERVICE_METHOD_VARIABLES[service_method]
    }


@router.get("/{template_code}")
async def get_template_variables(
    template_code: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Obtiene las variables disponibles para un template específico.

    DEPRECATED: Usar /by-method/{service_method} para obtener variables por service method.
    Este endpoint mantiene compatibilidad con código legacy.

    Args:
        template_code: Código del template (ej: daily_business_summary)

    Returns:
        Metadata de variables para el template específico
    """
    # Mapeo de template_code legacy a service_method
    LEGACY_CODE_TO_METHOD = {
        "daily_business_summary": "get_daily_summary",
        "weekly_business_summary": "get_weekly_summary",
    }

    service_method = LEGACY_CODE_TO_METHOD.get(template_code, template_code)

    if service_method in SERVICE_METHOD_VARIABLES:
        return {
            "success": True,
            "data": SERVICE_METHOD_VARIABLES[service_method]
        }

    return {
        "success": False,
        "error": f"No se encontraron variables para el template '{template_code}'",
        "data": {
            "name": "Template Personalizado",
            "description": "No hay variables predefinidas para este template",
            "variables": []
        }
    }
