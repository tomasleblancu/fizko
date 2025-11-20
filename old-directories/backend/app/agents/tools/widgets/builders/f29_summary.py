"""F29 Summary Widget - Simple summary card based on .widget template."""

from __future__ import annotations

from typing import Any

try:
    from chatkit.widgets import Badge, Box, Card, Col, Divider, Icon, Row, Spacer, Text, Title, WidgetRoot
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False
    # Fallback types for type hints
    Card = Any  # type: ignore
    WidgetRoot = Any  # type: ignore
    Box = Any  # type: ignore
    Row = Any  # type: ignore
    Col = Any  # type: ignore
    Text = Any  # type: ignore
    Title = Any  # type: ignore
    Badge = Any  # type: ignore
    Divider = Any  # type: ignore
    Icon = Any  # type: ignore
    Spacer = Any  # type: ignore


def create_f29_summary_widget(
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
) -> WidgetRoot | None:
    """
    Create a simple F29 summary widget based on the .widget template.

    This matches the structure from the Widget Builder template:
    - Header with title, period badge
    - Company name and RUT
    - Total determinado (with payment badge)
    - Total a pagar
    - Fecha de presentación
    - Details: Folio, Banco·Medio, Estado

    Args:
        company: Company name
        rut: Company RUT
        periodo: Period (e.g., "Ene 2025")
        folio: Form folio number
        total_determinado: Total amount determined (formatted, e.g., "CLP $58.123")
        total_a_pagar_plazo: Total to pay (formatted)
        estado: Form status
        fecha_presentacion: Presentation date (formatted)
        banco: Bank name
        medio_pago: Payment method
        tipo_declaracion: Declaration type (Primitiva, Rectificativa, etc.)
        is_paid: Whether the form is paid

    Returns:
        Card widget with F29 summary, or None if widgets not available
    """
    if not WIDGETS_AVAILABLE:
        return None

    # Build the widget matching the template structure
    return Card(
        size="sm",
        children=[
            # Header section
            Col(
                gap=2,
                children=[
                    Row(
                        children=[
                            Title(value="Resumen F29", size="md"),
                            Spacer(),
                            Badge(label=periodo, color="info"),
                        ]
                    ),
                    Text(value=company, weight="semibold"),
                    Text(value=f"RUT {rut}", size="sm", color="secondary"),
                ]
            ),

            Divider(),

            # Main metrics section
            Col(
                gap=3,
                children=[
                    # Total determinado
                    Row(
                        gap=3,
                        children=[
                            Box(
                                background="green-100",
                                radius="sm",
                                padding=2,
                                children=[
                                    Icon(name="chart", color="success"),
                                ]
                            ),
                            Col(
                                children=[
                                    Text(value="Total determinado", size="sm", color="secondary"),
                                    Text(value=total_determinado, weight="semibold"),
                                ]
                            ),
                            Spacer(),
                            Badge(label="Pagado" if is_paid else "Pendiente",
                                  color="success" if is_paid else "warning"),
                        ]
                    ),

                    # Total a pagar
                    Row(
                        gap=3,
                        children=[
                            Box(
                                background="alpha-10",
                                radius="sm",
                                padding=2,
                                children=[
                                    Icon(name="check-circle-filled" if is_paid else "circle-question",
                                         color="success" if is_paid else "warning"),
                                ]
                            ),
                            Col(
                                children=[
                                    Text(value="Total a pagar (plazo legal)", size="sm", color="secondary"),
                                    Text(value=total_a_pagar_plazo, weight="semibold"),
                                ]
                            ),
                        ]
                    ),

                    # Fecha de presentación
                    Row(
                        gap=3,
                        children=[
                            Box(
                                background="alpha-10",
                                radius="sm",
                                padding=2,
                                children=[
                                    Icon(name="calendar"),
                                ]
                            ),
                            Col(
                                children=[
                                    Text(value="Fecha de presentación", size="sm", color="secondary"),
                                    Text(value=fecha_presentacion, weight="semibold"),
                                ]
                            ),
                            Spacer(),
                            Badge(label=tipo_declaracion, color="secondary"),
                        ]
                    ),
                ]
            ),

            Divider(),

            # Details section
            Col(
                gap=2,
                children=[
                    Row(
                        children=[
                            Text(value="Folio", size="sm", color="secondary"),
                            Spacer(),
                            Text(value=folio, size="sm"),
                        ]
                    ),
                    Row(
                        children=[
                            Text(value="Banco · Medio", size="sm", color="secondary"),
                            Spacer(),
                            Text(value=f"{banco} · {medio_pago}", size="sm"),
                        ]
                    ),
                    Row(
                        children=[
                            Text(value="Estado", size="sm", color="secondary"),
                            Spacer(),
                            Text(value=estado, size="sm"),
                        ]
                    ),
                ]
            ),
        ]
    )


def f29_summary_widget_copy_text(
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
) -> str:
    """
    Generate human-readable fallback text for the F29 summary widget.

    Returns:
        Formatted text representation of the F29 summary
    """
    status_indicator = "✅ Pagado" if is_paid else "⏳ Pendiente"

    lines = [
        f"Resumen F29 - {periodo}",
        f"{company}",
        f"RUT {rut}",
        "",
        "📊 MONTOS",
        f"Total determinado: {total_determinado} [{status_indicator}]",
        f"Total a pagar (plazo legal): {total_a_pagar_plazo}",
        "",
        "📅 PRESENTACIÓN",
        f"Fecha: {fecha_presentacion}",
        f"Tipo: {tipo_declaracion}",
        "",
        "📋 DETALLES",
        f"Folio: {folio}",
        f"Banco · Medio: {banco} · {medio_pago}",
        f"Estado: {estado}",
    ]

    return "\n".join(lines)
