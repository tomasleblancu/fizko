"""Tools for displaying tax calculation widgets."""

from __future__ import annotations

import logging
from typing import Any

from agents import RunContextWrapper, function_tool

from ..context import FizkoContext
from ..widgets import (
    create_tax_calculation_widget,
    tax_calculation_widget_copy_text,
    create_document_detail_widget,
    document_detail_widget_copy_text,
)

logger = logging.getLogger(__name__)


@function_tool(
    strict_mode=False,
    description_override="Muestra un widget visual con el desglose detallado del cálculo de impuestos mensuales. Usa esta herramienta para mostrar visualmente cómo se calculó el impuesto mensual a partir del IVA cobrado, IVA pagado y el crédito del mes anterior.",
)
async def show_tax_calculation_widget(
    ctx: RunContextWrapper[FizkoContext],
    iva_collected: float,
    iva_paid: float,
    monthly_tax: float,
    period: str,
    previous_month_credit: float | None = None,
) -> dict[str, Any]:
    """
    Muestra un widget interactivo con el desglose detallado del cálculo de impuestos.

    Esta herramienta renderiza un widget visual que muestra paso a paso cómo se calculó
    el impuesto mensual, incluyendo:
    - IVA Cobrado (débito fiscal)
    - IVA Pagado (crédito fiscal)
    - IVA Neto (diferencia entre cobrado y pagado)
    - Crédito del mes anterior (código 077 del F29)
    - Impuesto final a pagar

    Args:
        iva_collected: IVA cobrado en ventas (débito fiscal)
        iva_paid: IVA pagado en compras (crédito fiscal)
        monthly_tax: Impuesto mensual final a pagar (después de aplicar créditos)
        period: Período del cálculo en formato legible (ej: "Oct 2025")
        previous_month_credit: Crédito fiscal del mes anterior (código 077). Opcional.

    Returns:
        Diccionario con confirmación de que el widget fue mostrado

    Examples:
        >>> await show_tax_calculation_widget(
        ...     ctx=ctx,
        ...     iva_collected=1340928.0,
        ...     iva_paid=500290.0,
        ...     previous_month_credit=1719528.0,
        ...     monthly_tax=0.0,
        ...     period="Oct 2025"
        ... )
        {'widget_shown': True, 'period': 'Oct 2025'}
    """
    logger.info(
        f"[TaxWidget] Showing tax calculation widget for period {period} "
        f"(IVA: {iva_collected} - {iva_paid}, Credit: {previous_month_credit}, "
        f"Tax: {monthly_tax})"
    )

    try:
        # Create the widget
        widget = create_tax_calculation_widget(
            iva_collected=iva_collected,
            iva_paid=iva_paid,
            previous_month_credit=previous_month_credit,
            monthly_tax=monthly_tax,
            period=period,
        )

        if widget is None:
            logger.warning("[TaxWidget] Widgets not available, skipping")
            return {
                "widget_shown": False,
                "error": "Widgets not available",
                "period": period,
            }

        # Create fallback copy text
        copy_text = tax_calculation_widget_copy_text(
            iva_collected=iva_collected,
            iva_paid=iva_paid,
            previous_month_credit=previous_month_credit,
            monthly_tax=monthly_tax,
            period=period,
        )

        logger.info("[TaxWidget] Streaming widget to client")

        # Stream the widget to the client
        await ctx.context.stream_widget(widget, copy_text=copy_text)

        logger.info("[TaxWidget] Widget streamed successfully")

        return {
            "widget_shown": True,
            "period": period,
            "iva_collected": iva_collected,
            "iva_paid": iva_paid,
            "previous_month_credit": previous_month_credit,
            "monthly_tax": monthly_tax,
        }

    except Exception as e:
        logger.error(f"[TaxWidget] Error showing widget: {e}", exc_info=True)
        return {
            "widget_shown": False,
            "error": str(e),
            "period": period,
        }


@function_tool(
    strict_mode=False,
    description_override="Muestra un widget visual con el detalle completo de un documento tributario (factura, boleta, nota de crédito, etc.). Usa esta herramienta para mostrar información del documento de forma visual y estructurada.",
)
async def show_document_detail_widget(
    ctx: RunContextWrapper[FizkoContext],
    document_type_name: str,
    folio: str,
    issue_date: str,
    status: str,
    net_amount: float,
    tax_amount: float,
    total_amount: float,
    contact_name: str | None = None,
    contact_rut: str | None = None,
    contact_label: str = "Contacto",
    sii_track_id: str | None = None,
    is_sales: bool = True,
) -> dict[str, Any]:
    """
    Muestra un widget interactivo con el detalle completo de un documento tributario.

    Esta herramienta renderiza un widget visual que muestra toda la información
    relevante de un documento:
    - Tipo de documento y folio
    - Fecha de emisión y estado
    - Montos (neto, IVA, total)
    - Información del contacto (cliente o proveedor)
    - Track ID del SII (si existe)

    Args:
        document_type_name: Nombre legible del tipo de documento (ej: "Factura de Venta")
        folio: Número de folio del documento
        issue_date: Fecha de emisión (formato ISO)
        status: Estado del documento (ej: "Emitida", "Aceptada", "Pagada")
        net_amount: Monto neto (sin impuestos)
        tax_amount: Monto del IVA
        total_amount: Monto total del documento
        contact_name: Nombre o razón social del contacto (opcional)
        contact_rut: RUT del contacto (opcional)
        contact_label: Etiqueta para el contacto ("Cliente", "Proveedor", etc.)
        sii_track_id: ID de seguimiento del SII (opcional)
        is_sales: True para documentos de venta, False para compras

    Returns:
        Diccionario con confirmación de que el widget fue mostrado

    Examples:
        >>> await show_document_detail_widget(
        ...     ctx=ctx,
        ...     document_type_name="Factura de Venta",
        ...     folio="12345",
        ...     issue_date="2025-10-15",
        ...     status="Emitida",
        ...     net_amount=850000.0,
        ...     tax_amount=161500.0,
        ...     total_amount=1011500.0,
        ...     contact_name="Empresa Cliente SpA",
        ...     contact_rut="76.123.456-7",
        ...     contact_label="Cliente",
        ...     is_sales=True
        ... )
        {'widget_shown': True, 'folio': '12345'}
    """
    logger.info(
        f"[DocumentWidget] Showing document detail widget for {document_type_name} "
        f"folio {folio}"
    )

    try:
        # Create the widget
        widget = create_document_detail_widget(
            document_type_name=document_type_name,
            folio=folio,
            issue_date=issue_date,
            status=status,
            net_amount=net_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            contact_name=contact_name,
            contact_rut=contact_rut,
            contact_label=contact_label,
            sii_track_id=sii_track_id,
            is_sales=is_sales,
        )

        if widget is None:
            logger.warning("[DocumentWidget] Widgets not available, skipping")
            return {
                "widget_shown": False,
                "error": "Widgets not available",
                "folio": folio,
            }

        # Create fallback copy text
        copy_text = document_detail_widget_copy_text(
            document_type_name=document_type_name,
            folio=folio,
            issue_date=issue_date,
            status=status,
            net_amount=net_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            contact_name=contact_name,
            contact_rut=contact_rut,
            contact_label=contact_label,
            sii_track_id=sii_track_id,
        )

        logger.info("[DocumentWidget] Streaming widget to client")

        # Stream the widget to the client
        await ctx.context.stream_widget(widget, copy_text=copy_text)

        logger.info("[DocumentWidget] Widget streamed successfully")

        return {
            "widget_shown": True,
            "document_type": document_type_name,
            "folio": folio,
            "total_amount": total_amount,
        }

    except Exception as e:
        logger.error(f"[DocumentWidget] Error showing widget: {e}", exc_info=True)
        return {
            "widget_shown": False,
            "error": str(e),
            "folio": folio,
        }
