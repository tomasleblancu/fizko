"""Document Detail Widget - Displays tax document information."""

from __future__ import annotations

from typing import Any

try:
    from chatkit.widgets import Box, Card, Col, Row, Text, WidgetRoot
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False
    # Fallback types for type hints
    Card = Any  # type: ignore
    WidgetRoot = Any  # type: ignore
    Box = Any  # type: ignore
    Col = Any  # type: ignore
    Row = Any  # type: ignore
    Text = Any  # type: ignore


def create_document_detail_widget(
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
) -> WidgetRoot | None:
    """
    Create a widget displaying document details.

    Args:
        document_type_name: Human-readable document type (e.g., "Factura de Venta")
        folio: Document folio number
        issue_date: Issue date (ISO format)
        status: Document status
        net_amount: Net amount (before tax)
        tax_amount: Tax amount (IVA)
        total_amount: Total amount
        contact_name: Contact business name (optional)
        contact_rut: Contact RUT (optional)
        contact_label: Label for contact ("Cliente", "Proveedor", etc.)
        sii_track_id: SII tracking ID (optional)
        is_sales: True for sales documents, False for purchase documents

    Returns:
        Card widget with document details, or None if widgets not available
    """
    if not WIDGETS_AVAILABLE:
        return None

    # Format currency
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    # Parse date for better formatting
    from datetime import datetime
    try:
        date_obj = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
        formatted_date = date_obj.strftime("%d %b %Y")
    except:
        formatted_date = issue_date

    # Icon based on document type
    icon = "📄" if is_sales else "📥"

    rows = []

    # Header with document type and folio
    rows.append(
        Box(
            padding=4,
            background="surface-tertiary",
            children=[
                Col(
                    gap=1,
                    children=[
                        Text(
                            value=f"{icon} {document_type_name}",
                            size="lg",
                            weight="semibold",
                        ),
                        Row(
                            gap=2,
                            children=[
                                Text(
                                    value=f"Folio: {folio}",
                                    size="sm",
                                    color="secondary",
                                ),
                                Text(
                                    value="•",
                                    size="sm",
                                    color="tertiary",
                                ),
                                Text(
                                    value=formatted_date,
                                    size="sm",
                                    color="secondary",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
    )

    # Content
    content_rows = []

    # Status badge
    status_color = "success" if status.lower() in ["emitida", "aceptada", "pagada"] else "secondary"
    content_rows.append(
        Box(
            padding={"bottom": 3},
            children=[
                Row(
                    align="center",
                    gap=2,
                    children=[
                        Text(value="Estado:", size="sm", weight="medium"),
                        Box(
                            padding={"top": 1, "bottom": 1, "left": 2, "right": 2},
                            radius="md",
                            background="surface-tertiary",
                            children=[
                                Text(
                                    value=status,
                                    size="xs",
                                    weight="medium",
                                    color=status_color,
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )
    )

    # Amounts section
    content_rows.append(
        Col(
            gap=1,
            children=[
                Text(value="💰 Montos", size="sm", weight="semibold", color="secondary"),
                Box(
                    padding={"top": 2},
                    gap=1,
                    children=[
                        Row(
                            justify="between",
                            children=[
                                Text(value="Neto", size="sm"),
                                Text(value=fmt(net_amount), size="sm", weight="medium"),
                            ],
                        ),
                        Row(
                            justify="between",
                            children=[
                                Text(value="IVA", size="sm", color="tertiary"),
                                Text(value=fmt(tax_amount), size="sm", color="tertiary"),
                            ],
                        ),
                        Box(
                            padding={"top": 2},
                            border={"top": 2},
                            borderColor="border-primary",
                            children=[
                                Row(
                                    justify="between",
                                    children=[
                                        Text(value="Total", size="md", weight="bold"),
                                        Text(value=fmt(total_amount), size="md", weight="bold"),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
    )

    # Contact information (if available)
    if contact_name or contact_rut:
        content_rows.append(
            Box(
                padding={"top": 3},
                border={"top": 1},
                borderColor="border-secondary",
                children=[
                    Col(
                        gap=1,
                        children=[
                            Text(value=f"👤 {contact_label}", size="sm", weight="semibold", color="secondary"),
                            Box(
                                padding={"top": 1},
                                gap=1,
                                children=[
                                    Text(
                                        value=contact_name or "N/A",
                                        size="sm",
                                        weight="medium",
                                    ) if contact_name else None,
                                    Text(
                                        value=f"RUT: {contact_rut}" if contact_rut else "RUT: N/A",
                                        size="xs",
                                        color="tertiary",
                                    ),
                                ] if contact_name else [
                                    Text(
                                        value=f"RUT: {contact_rut}" if contact_rut else "RUT: N/A",
                                        size="xs",
                                        color="tertiary",
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            )
        )

    # SII Track ID (if available)
    if sii_track_id:
        content_rows.append(
            Box(
                padding={"top": 2},
                children=[
                    Text(
                        value=f"🔗 Track ID SII: {sii_track_id}",
                        size="xs",
                        color="tertiary",
                    )
                ],
            )
        )

    # Wrap content
    rows.append(
        Box(
            padding=4,
            gap=3,
            children=content_rows,
        )
    )

    return Card(
        key="document_detail",
        padding=0,
        children=rows,
    )


def document_detail_widget_copy_text(
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
) -> str:
    """
    Generate human-readable fallback text for the document detail widget.

    Args:
        document_type_name: Human-readable document type
        folio: Document folio
        issue_date: Issue date
        status: Document status
        net_amount: Net amount
        tax_amount: Tax amount
        total_amount: Total amount
        contact_name: Contact name (optional)
        contact_rut: Contact RUT (optional)
        contact_label: Label for contact
        sii_track_id: SII track ID (optional)

    Returns:
        Formatted text representation
    """
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    lines = [
        f"{document_type_name} - Folio {folio}",
        f"Fecha: {issue_date}",
        f"Estado: {status}",
        "",
        "Montos:",
        f"  Neto: {fmt(net_amount)}",
        f"  IVA: {fmt(tax_amount)}",
        f"  Total: {fmt(total_amount)}",
    ]

    if contact_name or contact_rut:
        lines.append("")
        lines.append(f"{contact_label}:")
        if contact_name:
            lines.append(f"  {contact_name}")
        if contact_rut:
            lines.append(f"  RUT: {contact_rut}")

    if sii_track_id:
        lines.append("")
        lines.append(f"Track ID SII: {sii_track_id}")

    return "\n".join(lines)
