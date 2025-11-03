"""Tax Calculation Widget - Displays tax breakdown and calculations."""

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


def create_tax_calculation_widget(
    iva_collected: float,
    iva_paid: float,
    previous_month_credit: float | None,
    monthly_tax: float,
    period: str,
    ppm: float | None = None,
    retencion: float | None = None,
    impuesto_trabajadores: float | None = None,
) -> WidgetRoot | None:
    """
    Create a widget displaying the tax calculation breakdown.

    Args:
        iva_collected: IVA débito fiscal (IVA cobrado)
        iva_paid: IVA crédito fiscal (IVA pagado)
        previous_month_credit: Crédito del mes anterior from F29
        monthly_tax: Final tax amount to pay
        period: Period string (e.g., "Oct 2025")
        ppm: PPM (Pago Provisional Mensual) - adelanto para impuesto anual
        retencion: Retención de honorarios
        impuesto_trabajadores: Impuesto asociado a sueldos

    Returns:
        Card widget with the tax calculation breakdown, or None if widgets not available
    """
    if not WIDGETS_AVAILABLE:
        return None

    # Format currency
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    # Calculate IVA neto
    iva_neto = iva_collected - iva_paid

    # Build widget rows
    rows = []

    # Header
    rows.append(
        Box(
            padding=4,
            background="surface-tertiary",
            children=[
                Text(
                    value=f"💰 Cálculo de Impuesto - {period}",
                    size="lg",
                    weight="semibold",
                )
            ],
        )
    )

    # Content section
    content_rows = []

    # IVA Collected
    content_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="IVA Cobrado", size="sm"),
                Text(value=fmt(iva_collected), size="sm", weight="medium"),
            ],
        )
    )

    # IVA Paid
    content_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="IVA Pagado", size="sm", color="tertiary"),
                Text(value=f"-{fmt(iva_paid)}", size="sm", color="tertiary"),
            ],
        )
    )

    # Previous month credit (always show)
    content_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="IVA Crédito Mes Anterior", size="sm", color="tertiary"),
                Text(value=f"-{fmt(previous_month_credit or 0.0)}", size="sm", color="tertiary"),
            ],
        )
    )

    # IVA Neto
    content_rows.append(
        Box(
            padding={"top": 2, "bottom": 2},
            border={"top": 1, "bottom": 1},
            borderColor="border-secondary",
            children=[
                Row(
                    justify="between",
                    align="center",
                    children=[
                        Text(value="IVA Neto", size="sm", weight="semibold"),
                        Text(value=fmt(iva_neto), size="sm", weight="semibold"),
                    ],
                )
            ],
        )
    )

    # Additional taxes section
    # PPM
    if ppm is not None:
        content_rows.append(
            Row(
                justify="between",
                align="center",
                children=[
                    Text(value="PPM (Adelanto Impuesto Anual)", size="sm", color="tertiary"),
                    Text(value=fmt(ppm), size="sm", color="tertiary"),
                ],
            )
        )

    # Retención
    if retencion is not None:
        content_rows.append(
            Row(
                justify="between",
                align="center",
                children=[
                    Text(value="Retención (Honorarios)", size="sm", color="tertiary"),
                    Text(value=fmt(retencion), size="sm", color="tertiary"),
                ],
            )
        )

    # Impuesto de Trabajadores
    if impuesto_trabajadores is not None:
        content_rows.append(
            Row(
                justify="between",
                align="center",
                children=[
                    Text(value="Impuesto Trabajadores", size="sm", color="tertiary"),
                    Text(value=fmt(impuesto_trabajadores), size="sm", color="tertiary"),
                ],
            )
        )

    # Final result
    content_rows.append(
        Box(
            padding={"top": 3},
            border={"top": 2},
            borderColor="border-primary",
            children=[
                Row(
                    justify="between",
                    align="center",
                    children=[
                        Text(value="Impuesto a Pagar", size="lg", weight="bold"),
                        Text(value=fmt(monthly_tax), size="lg", weight="bold"),
                    ],
                )
            ],
        )
    )

    # Add note if there's a remaining credit
    if previous_month_credit and iva_neto < previous_month_credit:
        remaining_credit = previous_month_credit - iva_neto
        content_rows.append(
            Box(
                padding={"top": 2},
                children=[
                    Text(
                        value=f"ℹ️ Remanente a favor: {fmt(remaining_credit)} para el próximo mes",
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
            gap=2,
            children=content_rows,
        )
    )

    return Card(
        key="tax_calculation",
        padding=0,
        children=rows,
    )


def tax_calculation_widget_copy_text(
    iva_collected: float,
    iva_paid: float,
    previous_month_credit: float | None,
    monthly_tax: float,
    period: str,
    ppm: float | None = None,
    retencion: float | None = None,
    impuesto_trabajadores: float | None = None,
) -> str:
    """
    Generate human-readable fallback text for the tax calculation widget.

    Args:
        iva_collected: IVA débito fiscal (IVA cobrado)
        iva_paid: IVA crédito fiscal (IVA pagado)
        previous_month_credit: Crédito del mes anterior from F29
        monthly_tax: Final tax amount to pay
        period: Period string (e.g., "Oct 2025")
        ppm: PPM (Pago Provisional Mensual)
        retencion: Retención de honorarios
        impuesto_trabajadores: Impuesto asociado a sueldos

    Returns:
        Formatted text representation of the tax calculation
    """
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    iva_neto = iva_collected - iva_paid

    lines = [
        f"Cálculo de Impuesto - {period}",
        "",
        f"IVA Cobrado: {fmt(iva_collected)}",
        f"IVA Pagado: -{fmt(iva_paid)}",
        f"IVA Crédito Mes Anterior: -{fmt(previous_month_credit or 0.0)}",
        f"IVA Neto: {fmt(iva_neto)}",
    ]

    if ppm is not None:
        lines.append(f"PPM (Adelanto Impuesto Anual): {fmt(ppm)}")

    if retencion is not None:
        lines.append(f"Retención (Honorarios): {fmt(retencion)}")

    if impuesto_trabajadores is not None:
        lines.append(f"Impuesto Trabajadores: {fmt(impuesto_trabajadores)}")

    lines.append("")
    lines.append(f"Impuesto a Pagar: {fmt(monthly_tax)}")

    if previous_month_credit and iva_neto < previous_month_credit:
        remaining_credit = previous_month_credit - iva_neto
        lines.append("")
        lines.append(f"Remanente a favor: {fmt(remaining_credit)} para el próximo mes")

    return "\n".join(lines)
