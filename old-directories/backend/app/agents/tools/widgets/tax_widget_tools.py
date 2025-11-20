"""Tools for displaying tax calculation widgets."""

from __future__ import annotations

import logging
from typing import Any

from agents import RunContextWrapper, function_tool

from ...core import FizkoContext
from .widgets import (
    create_tax_calculation_widget,
    tax_calculation_widget_copy_text,
    create_document_detail_widget,
    document_detail_widget_copy_text,
    create_f29_detail_widget,
    f29_detail_widget_copy_text,
    create_f29_summary_widget,
    f29_summary_widget_copy_text,
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


@function_tool(
    strict_mode=False,
    description_override="Muestra un widget visual con el detalle completo del Formulario 29 (F29). Usa esta herramienta para mostrar el desglose de ventas, compras, y cálculo de IVA de forma visual y estructurada.",
)
async def show_f29_detail_widget(
    ctx: RunContextWrapper[FizkoContext],
    folio: str,
    period: str,
    status: str,
    submission_date: str | None,
    total_sales: float,
    taxable_sales: float,
    exempt_sales: float,
    sales_tax: float,
    total_purchases: float,
    taxable_purchases: float,
    purchases_tax: float,
    iva_to_pay: float,
    iva_credit: float,
    net_iva: float,
    previous_month_credit: float | None = None,
    pdf_available: bool = False,
    pdf_url: str | None = None,
) -> dict[str, Any]:
    """
    Muestra un widget interactivo con el detalle completo del Formulario 29 (F29).

    Esta herramienta renderiza un widget visual que muestra toda la información
    del formulario F29:
    - Información del formulario (folio, período, estado)
    - Ventas (totales, afectas, exentas, IVA débito)
    - Compras (totales, afectas, IVA crédito)
    - Cálculo final de IVA (a pagar o remanente)
    - Crédito del mes anterior si aplica

    Args:
        folio: Número de folio del formulario
        period: Período en formato "YYYY-MM"
        status: Estado del formulario (Vigente, Rectificado, Anulado)
        submission_date: Fecha de presentación (formato ISO o legible)
        total_sales: Monto total de ventas
        taxable_sales: Monto de ventas afectas a IVA
        exempt_sales: Monto de ventas exentas de IVA
        sales_tax: IVA débito fiscal (de ventas)
        total_purchases: Monto total de compras
        taxable_purchases: Monto de compras afectas a IVA
        purchases_tax: IVA crédito fiscal (de compras)
        iva_to_pay: IVA débito fiscal total
        iva_credit: IVA crédito fiscal total
        net_iva: IVA neto (positivo = a pagar, negativo = remanente)
        previous_month_credit: Crédito del mes anterior (código 077) - opcional
        pdf_available: Si el PDF está disponible
        pdf_url: URL del PDF (opcional)

    Returns:
        Diccionario con confirmación de que el widget fue mostrado

    Examples:
        >>> await show_f29_detail_widget(
        ...     ctx=ctx,
        ...     folio="123456789",
        ...     period="2025-10",
        ...     status="Vigente",
        ...     submission_date="2025-11-15",
        ...     total_sales=10000000.0,
        ...     taxable_sales=9500000.0,
        ...     exempt_sales=500000.0,
        ...     sales_tax=1805000.0,
        ...     total_purchases=5000000.0,
        ...     taxable_purchases=5000000.0,
        ...     purchases_tax=950000.0,
        ...     iva_to_pay=1805000.0,
        ...     iva_credit=950000.0,
        ...     net_iva=855000.0,
        ...     previous_month_credit=0.0,
        ...     pdf_available=True
        ... )
        {'widget_shown': True, 'folio': '123456789', 'period': '2025-10'}
    """
    logger.info(
        f"[F29Widget] Showing F29 detail widget for folio {folio}, period {period}"
    )

    try:
        # Create the widget
        widget = create_f29_detail_widget(
            folio=folio,
            period=period,
            status=status,
            submission_date=submission_date,
            total_sales=total_sales,
            taxable_sales=taxable_sales,
            exempt_sales=exempt_sales,
            sales_tax=sales_tax,
            total_purchases=total_purchases,
            taxable_purchases=taxable_purchases,
            purchases_tax=purchases_tax,
            iva_to_pay=iva_to_pay,
            iva_credit=iva_credit,
            net_iva=net_iva,
            previous_month_credit=previous_month_credit,
            pdf_available=pdf_available,
            pdf_url=pdf_url,
        )

        if widget is None:
            logger.warning("[F29Widget] Widgets not available, skipping")
            return {
                "widget_shown": False,
                "error": "Widgets not available",
                "folio": folio,
            }

        # Create fallback copy text
        copy_text = f29_detail_widget_copy_text(
            folio=folio,
            period=period,
            status=status,
            submission_date=submission_date,
            total_sales=total_sales,
            taxable_sales=taxable_sales,
            exempt_sales=exempt_sales,
            sales_tax=sales_tax,
            total_purchases=total_purchases,
            taxable_purchases=taxable_purchases,
            purchases_tax=purchases_tax,
            iva_to_pay=iva_to_pay,
            iva_credit=iva_credit,
            net_iva=net_iva,
            previous_month_credit=previous_month_credit,
            pdf_available=pdf_available,
            pdf_url=pdf_url,
        )

        logger.info("[F29Widget] Streaming widget to client")

        # Stream the widget to the client
        await ctx.context.stream_widget(widget, copy_text=copy_text)

        logger.info("[F29Widget] Widget streamed successfully")

        return {
            "widget_shown": True,
            "folio": folio,
            "period": period,
            "net_iva": net_iva,
        }

    except Exception as e:
        logger.error(f"[F29Widget] Error showing widget: {e}", exc_info=True)
        return {
            "widget_shown": False,
            "error": str(e),
            "folio": folio,
        }


@function_tool(
    strict_mode=False,
    description_override="Muestra un widget de resumen visual del Formulario 29 (F29) con la información principal. Usa esta herramienta para mostrar un resumen ejecutivo del F29 con los montos clave y detalles de presentación.",
)
async def show_f29_summary_widget(
    ctx: RunContextWrapper[FizkoContext],
    company: str,
    rut: str,
    periodo: str,
    folio: str,
    total_determinado: str,
    total_a_pagar_plazo: str,
    estado: str,
    fecha_presentacion: str,
    banco: str = "N/A",
    medio_pago: str = "N/A",
    tipo_declaracion: str = "Primitiva",
    is_paid: bool = True,
) -> dict[str, Any]:
    """
    Muestra un widget de resumen del Formulario 29 (F29).

    Esta herramienta muestra un resumen ejecutivo del F29 con:
    - Encabezado con empresa, RUT y período
    - Total determinado con indicador de pago
    - Total a pagar en plazo legal
    - Fecha de presentación y tipo de declaración
    - Detalles: folio, banco, medio de pago, estado

    Args:
        company: Nombre de la empresa
        rut: RUT de la empresa (formato "XX.XXX.XXX-X")
        periodo: Período (formato legible, ej: "Ene 2025")
        folio: Número de folio del formulario
        total_determinado: Total determinado (formato: "CLP $XX.XXX")
        total_a_pagar_plazo: Total a pagar en plazo legal (formato: "CLP $XX.XXX")
        estado: Estado del formulario (ej: "Recibida y pagada por internet")
        fecha_presentacion: Fecha de presentación (formato: "DD/MM/YYYY")
        banco: Nombre del banco
        medio_pago: Medio de pago (ej: "PEL", "PAC", etc.)
        tipo_declaracion: Tipo de declaración (Primitiva, Rectificativa, etc.)
        is_paid: Si el formulario está pagado

    Returns:
        Diccionario con confirmación de que el widget fue mostrado

    Examples:
        >>> await show_f29_summary_widget(
        ...     ctx=ctx,
        ...     company="COMERCIAL ATAL SPA",
        ...     rut="77.794.858-K",
        ...     periodo="Ene 2025",
        ...     folio="8104678626",
        ...     total_determinado="CLP $58.123",
        ...     total_a_pagar_plazo="CLP $58.123",
        ...     estado="Recibida y pagada por internet",
        ...     fecha_presentacion="20/02/2025",
        ...     banco="BICE",
        ...     medio_pago="PEL",
        ...     tipo_declaracion="Primitiva",
        ...     is_paid=True
        ... )
        {'widget_shown': True, 'folio': '8104678626'}
    """
    logger.info(
        f"[F29SummaryWidget] Showing F29 summary widget for folio {folio}, period {periodo}"
    )

    try:
        # Create the widget
        widget = create_f29_summary_widget(
            company=company,
            rut=rut,
            periodo=periodo,
            folio=folio,
            total_determinado=total_determinado,
            total_a_pagar_plazo=total_a_pagar_plazo,
            estado=estado,
            fecha_presentacion=fecha_presentacion,
            banco=banco,
            medio_pago=medio_pago,
            tipo_declaracion=tipo_declaracion,
            is_paid=is_paid,
        )

        if widget is None:
            logger.warning("[F29SummaryWidget] Widgets not available, skipping")
            return {
                "widget_shown": False,
                "error": "Widgets not available",
                "folio": folio,
            }

        # Create fallback copy text
        copy_text = f29_summary_widget_copy_text(
            company=company,
            rut=rut,
            periodo=periodo,
            folio=folio,
            total_determinado=total_determinado,
            total_a_pagar_plazo=total_a_pagar_plazo,
            estado=estado,
            fecha_presentacion=fecha_presentacion,
            banco=banco,
            medio_pago=medio_pago,
            tipo_declaracion=tipo_declaracion,
            is_paid=is_paid,
        )

        logger.info("[F29SummaryWidget] Streaming widget to client")

        # Stream the widget to the client
        await ctx.context.stream_widget(widget, copy_text=copy_text)

        logger.info("[F29SummaryWidget] Widget streamed successfully")

        return {
            "widget_shown": True,
            "folio": folio,
            "periodo": periodo,
        }

    except Exception as e:
        logger.error(f"[F29SummaryWidget] Error showing widget: {e}", exc_info=True)
        return {
            "widget_shown": False,
            "error": str(e),
            "folio": folio,
        }
