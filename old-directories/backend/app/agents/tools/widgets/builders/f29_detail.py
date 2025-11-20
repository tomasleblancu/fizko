"""F29 Detail Widget - Displays Form 29 components and breakdown."""

from __future__ import annotations

from typing import Any

try:
    from chatkit.widgets import Box, Card, Row, Text, WidgetRoot
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False
    # Fallback types for type hints
    Card = Any  # type: ignore
    WidgetRoot = Any  # type: ignore
    Box = Any  # type: ignore
    Row = Any  # type: ignore
    Text = Any  # type: ignore


def create_f29_detail_widget(
    folio: str,
    period: str,
    status: str,
    submission_date: str | None,
    # Ventas (Sales)
    total_sales: float,
    taxable_sales: float,
    exempt_sales: float,
    sales_tax: float,
    # Compras (Purchases)
    total_purchases: float,
    taxable_purchases: float,
    purchases_tax: float,
    # IVA Calculation
    iva_to_pay: float,
    iva_credit: float,
    net_iva: float,
    # Optional fields
    previous_month_credit: float | None = None,
    pdf_available: bool = False,
    pdf_url: str | None = None,
) -> WidgetRoot | None:
    """
    Create a widget displaying the F29 form detail breakdown.

    Args:
        folio: Form folio number
        period: Period in format "YYYY-MM"
        status: Form status (Vigente, Rectificado, Anulado)
        submission_date: Date when the form was submitted (ISO format)
        total_sales: Total sales amount
        taxable_sales: Taxable sales amount
        exempt_sales: Exempt sales amount
        sales_tax: Total IVA from sales (débito fiscal)
        total_purchases: Total purchases amount
        taxable_purchases: Taxable purchases amount
        purchases_tax: Total IVA from purchases (crédito fiscal)
        iva_to_pay: IVA débito fiscal (from sales)
        iva_credit: IVA crédito fiscal (from purchases)
        net_iva: Net IVA to pay or carry forward
        previous_month_credit: Credit from previous month (código 077)
        pdf_available: Whether PDF is available for download
        pdf_url: URL to the PDF file

    Returns:
        Card widget with the F29 detail breakdown, or None if widgets not available
    """
    if not WIDGETS_AVAILABLE:
        return None

    # Format currency
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    # Status emoji
    status_emoji = {
        "Vigente": "✅",
        "Rectificado": "🔄",
        "Anulado": "❌",
    }.get(status, "📄")

    rows = []

    # Header
    rows.append(
        Box(
            padding=4,
            background="surface-tertiary",
            children=[
                Text(
                    value=f"📋 Formulario F29 - {period}",
                    size="lg",
                    weight="semibold",
                ),
                Text(
                    value=f"Folio: {folio}",
                    size="sm",
                    color="secondary",
                ),
            ],
        )
    )

    # Content section
    content_rows = []

    # Status and submission info
    info_rows = []
    info_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="Estado", size="sm", weight="medium"),
                Text(value=f"{status_emoji} {status}", size="sm"),
            ],
        )
    )

    if submission_date:
        info_rows.append(
            Row(
                justify="between",
                align="center",
                children=[
                    Text(value="Fecha de presentación", size="sm", weight="medium"),
                    Text(value=submission_date, size="sm", color="secondary"),
                ],
            )
        )

    if pdf_available and pdf_url:
        info_rows.append(
            Row(
                justify="between",
                align="center",
                children=[
                    Text(value="PDF", size="sm", weight="medium"),
                    Text(value="✅ Disponible", size="sm", color="success"),
                ],
            )
        )

    content_rows.append(
        Box(
            padding={"bottom": 3},
            border={"bottom": 1},
            borderColor="border-secondary",
            gap=2,
            children=info_rows,
        )
    )

    # VENTAS (Sales) Section
    content_rows.append(
        Box(
            padding={"top": 3, "bottom": 2},
            children=[
                Text(value="📈 VENTAS", size="sm", weight="bold", color="primary")
            ],
        )
    )

    sales_rows = []
    sales_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="Ventas Totales", size="sm"),
                Text(value=fmt(total_sales), size="sm", weight="medium"),
            ],
        )
    )
    sales_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="  • Ventas Afectas", size="sm", color="secondary"),
                Text(value=fmt(taxable_sales), size="sm", color="secondary"),
            ],
        )
    )
    # Always show exempt sales, even if 0
    sales_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="  • Ventas Exentas", size="sm", color="secondary"),
                Text(value=fmt(exempt_sales), size="sm", color="secondary"),
            ],
        )
    )
    sales_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="IVA Débito Fiscal", size="sm", weight="semibold"),
                Text(value=fmt(sales_tax), size="sm", weight="semibold", color="primary"),
            ],
        )
    )

    content_rows.append(
        Box(
            padding={"bottom": 3},
            border={"bottom": 1},
            borderColor="border-secondary",
            gap=2,
            children=sales_rows,
        )
    )

    # COMPRAS (Purchases) Section
    content_rows.append(
        Box(
            padding={"top": 3, "bottom": 2},
            children=[
                Text(value="📉 COMPRAS", size="sm", weight="bold", color="primary")
            ],
        )
    )

    purchases_rows = []
    purchases_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="Compras Totales", size="sm"),
                Text(value=fmt(total_purchases), size="sm", weight="medium"),
            ],
        )
    )
    purchases_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="  • Compras Afectas", size="sm", color="secondary"),
                Text(value=fmt(taxable_purchases), size="sm", color="secondary"),
            ],
        )
    )
    purchases_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="IVA Crédito Fiscal", size="sm", weight="semibold"),
                Text(value=fmt(purchases_tax), size="sm", weight="semibold", color="success"),
            ],
        )
    )

    content_rows.append(
        Box(
            padding={"bottom": 3},
            border={"bottom": 1},
            borderColor="border-secondary",
            gap=2,
            children=purchases_rows,
        )
    )

    # IVA BALANCE Section
    content_rows.append(
        Box(
            padding={"top": 3, "bottom": 2},
            children=[
                Text(value="💰 CÁLCULO IVA", size="sm", weight="bold", color="primary")
            ],
        )
    )

    balance_rows = []
    balance_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="IVA Débito Fiscal (Ventas)", size="sm"),
                Text(value=fmt(iva_to_pay), size="sm", weight="medium"),
            ],
        )
    )
    balance_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="IVA Crédito Fiscal (Compras)", size="sm", color="tertiary"),
                Text(value=f"-{fmt(iva_credit)}", size="sm", color="tertiary"),
            ],
        )
    )

    # Always show previous month credit, even if 0
    credit_value = previous_month_credit if previous_month_credit is not None else 0
    balance_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="Crédito Mes Anterior (Cód. 077)", size="sm", color="tertiary"),
                Text(value=f"-{fmt(credit_value)}", size="sm", color="tertiary"),
            ],
        )
    )

    # Final IVA result
    is_credit = net_iva < 0
    iva_label = "Remanente a Favor" if is_credit else "IVA a Pagar"
    iva_value = abs(net_iva)
    iva_color = "success" if is_credit else "primary"

    balance_rows.append(
        Box(
            padding={"top": 2},
            border={"top": 2},
            borderColor="border-primary",
            children=[
                Row(
                    justify="between",
                    align="center",
                    children=[
                        Text(value=iva_label, size="md", weight="bold"),
                        Text(value=fmt(iva_value), size="md", weight="bold", color=iva_color),
                    ],
                )
            ],
        )
    )

    content_rows.append(
        Box(
            gap=2,
            children=balance_rows,
        )
    )

    # Note about credit
    if is_credit:
        content_rows.append(
            Box(
                padding={"top": 2},
                children=[
                    Text(
                        value="ℹ️ Este remanente se puede usar en el próximo mes como crédito (código 077)",
                        size="xs",
                        color="secondary",
                    )
                ],
            )
        )

    # Wrap content in a container
    rows.append(
        Box(
            padding=4,
            gap=1,
            children=content_rows,
        )
    )

    return Card(
        key="f29_detail",
        padding=0,
        children=rows,
    )


def f29_detail_widget_copy_text(
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
) -> str:
    """
    Generate human-readable fallback text for the F29 detail widget.

    Returns:
        Formatted text representation of the F29 form
    """
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    status_emoji = {
        "Vigente": "✅",
        "Rectificado": "🔄",
        "Anulado": "❌",
    }.get(status, "📄")

    lines = [
        f"Formulario F29 - {period}",
        f"Folio: {folio}",
        f"Estado: {status_emoji} {status}",
    ]

    if submission_date:
        lines.append(f"Fecha de presentación: {submission_date}")

    if pdf_available and pdf_url:
        lines.append("PDF: ✅ Disponible")

    lines.extend([
        "",
        "VENTAS",
        f"Ventas Totales: {fmt(total_sales)}",
        f"  • Ventas Afectas: {fmt(taxable_sales)}",
        f"  • Ventas Exentas: {fmt(exempt_sales)}",
        f"IVA Débito Fiscal: {fmt(sales_tax)}",
        "",
        "COMPRAS",
        f"Compras Totales: {fmt(total_purchases)}",
        f"  • Compras Afectas: {fmt(taxable_purchases)}",
        f"IVA Crédito Fiscal: {fmt(purchases_tax)}",
        "",
        "CÁLCULO IVA",
        f"IVA Débito Fiscal (Ventas): {fmt(iva_to_pay)}",
        f"IVA Crédito Fiscal (Compras): -{fmt(iva_credit)}",
    ])

    # Always show previous month credit, even if 0
    credit_value = previous_month_credit if previous_month_credit is not None else 0
    lines.append(f"Crédito Mes Anterior (Cód. 077): -{fmt(credit_value)}")

    lines.append("--------------------")

    is_credit = net_iva < 0
    iva_label = "Remanente a Favor" if is_credit else "IVA a Pagar"
    iva_value = abs(net_iva)

    lines.append(f"{iva_label}: {fmt(iva_value)}")

    if is_credit:
        lines.append("")
        lines.append("ℹ️ Este remanente se puede usar en el próximo mes como crédito (código 077)")

    return "\n".join(lines)
