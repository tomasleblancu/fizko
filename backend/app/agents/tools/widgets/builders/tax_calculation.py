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
    reverse_charge_withholding: float | None = None,
    impuesto_trabajadores: float | None = None,
    overdue_iva_credit: float | None = None,
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
        reverse_charge_withholding: Retención Cambio de Sujeto (código 46)
        impuesto_trabajadores: Impuesto asociado a sueldos
        overdue_iva_credit: IVA fuera de plazo (overdue IVA that can't be recovered)

    Returns:
        Card widget with the tax calculation breakdown, or None if widgets not available
    """
    if not WIDGETS_AVAILABLE:
        return None

    # Format currency
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    # Calculate IVA balance (can be negative)
    overdue_iva_value = overdue_iva_credit if overdue_iva_credit is not None else 0.0
    iva_balance = iva_collected - iva_paid - (previous_month_credit or 0.0) + overdue_iva_value
    iva_a_pagar = max(0.0, iva_balance)

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

    # Overdue IVA Credit (IVA fuera de plazo) - always show even if 0
    content_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="IVA Fuera de plazo", size="sm"),
                Text(value=f"+{fmt(overdue_iva_value)}", size="sm", weight="medium"),
            ],
        )
    )

    # IVA a Pagar (subtotal after IVA calculation)
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
                        Text(value="IVA a Pagar", size="sm", weight="semibold"),
                        Text(value=fmt(iva_a_pagar), size="sm", weight="semibold"),
                    ],
                )
            ],
        )
    )

    # Additional taxes section (these ADD to the total) - always show even if 0
    # PPM
    ppm_value = ppm if ppm is not None else 0.0
    content_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="PPM (Adelanto Impuesto Anual)", size="sm"),
                Text(value=f"+{fmt(ppm_value)}", size="sm", weight="medium"),
            ],
        )
    )

    # Retención
    retencion_value = retencion if retencion is not None else 0.0
    content_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="Retención (Honorarios)", size="sm"),
                Text(value=f"+{fmt(retencion_value)}", size="sm", weight="medium"),
            ],
        )
    )

    # Reverse Charge Withholding (Retención Cambio de Sujeto - código 46)
    reverse_charge_value = reverse_charge_withholding if reverse_charge_withholding is not None else 0.0
    content_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="Retención Cambio de Sujeto", size="sm"),
                Text(value=f"+{fmt(reverse_charge_value)}", size="sm", weight="medium"),
            ],
        )
    )

    # Impuesto de Trabajadores
    impuesto_trabajadores_value = impuesto_trabajadores if impuesto_trabajadores is not None else 0.0
    content_rows.append(
        Row(
            justify="between",
            align="center",
            children=[
                Text(value="Impuesto Trabajadores", size="sm"),
                Text(value=f"+{fmt(impuesto_trabajadores_value)}", size="sm", weight="medium"),
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

    # Add note if there's a remaining credit (when IVA balance is negative)
    if iva_balance < 0:
        remaining_credit = abs(iva_balance)
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
    reverse_charge_withholding: float | None = None,
    impuesto_trabajadores: float | None = None,
    overdue_iva_credit: float | None = None,
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
        reverse_charge_withholding: Retención Cambio de Sujeto (código 46)
        impuesto_trabajadores: Impuesto asociado a sueldos
        overdue_iva_credit: IVA fuera de plazo (overdue IVA that can't be recovered)

    Returns:
        Formatted text representation of the tax calculation
    """
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    # Calculate IVA balance and IVA a pagar
    overdue_iva_value = overdue_iva_credit if overdue_iva_credit is not None else 0.0
    iva_balance = iva_collected - iva_paid - (previous_month_credit or 0.0) + overdue_iva_value
    iva_a_pagar = max(0.0, iva_balance)

    lines = [
        f"Cálculo de Impuesto - {period}",
        "",
        f"IVA Cobrado: {fmt(iva_collected)}",
        f"IVA Pagado: -{fmt(iva_paid)}",
        f"IVA Crédito Mes Anterior: -{fmt(previous_month_credit or 0.0)}",
        f"IVA Fuera de plazo: +{fmt(overdue_iva_value)}",
        "--------------------",
        f"IVA a Pagar: {fmt(iva_a_pagar)}",
        "",
    ]

    # Always show additional taxes, even if 0
    ppm_value = ppm if ppm is not None else 0.0
    lines.append(f"PPM (Adelanto Impuesto Anual): +{fmt(ppm_value)}")

    retencion_value = retencion if retencion is not None else 0.0
    lines.append(f"Retención (Honorarios): +{fmt(retencion_value)}")

    reverse_charge_value = reverse_charge_withholding if reverse_charge_withholding is not None else 0.0
    lines.append(f"Retención Cambio de Sujeto: +{fmt(reverse_charge_value)}")

    impuesto_trabajadores_value = impuesto_trabajadores if impuesto_trabajadores is not None else 0.0
    lines.append(f"Impuesto Trabajadores: +{fmt(impuesto_trabajadores_value)}")

    lines.append("--------------------")
    lines.append(f"Impuesto a Pagar Total: {fmt(monthly_tax)}")

    if iva_balance < 0:
        remaining_credit = abs(iva_balance)
        lines.append("")
        lines.append(f"Remanente a favor: {fmt(remaining_credit)} para el próximo mes")

    return "\n".join(lines)
