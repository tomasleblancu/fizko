"""ChatKit Widgets for Fizko - Rich UI components for agent responses."""

from __future__ import annotations

from typing import Any

try:
    from chatkit.actions import ActionConfig
    from chatkit.widgets import Box, Button, Card, Col, Divider, Row, Text, WidgetRoot
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
    Button = Any  # type: ignore
    Divider = Any  # type: ignore
    ActionConfig = Any  # type: ignore


def create_tax_calculation_widget(
    iva_collected: float,
    iva_paid: float,
    previous_month_credit: float | None,
    monthly_tax: float,
    period: str,
) -> WidgetRoot | None:
    """
    Create a widget displaying the tax calculation breakdown.

    Args:
        iva_collected: IVA débito fiscal (IVA cobrado)
        iva_paid: IVA crédito fiscal (IVA pagado)
        previous_month_credit: Crédito del mes anterior from F29
        monthly_tax: Final tax amount to pay
        period: Period string (e.g., "Oct 2025")

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

    # Previous month credit if available
    if previous_month_credit is not None:
        content_rows.append(
            Row(
                justify="between",
                align="center",
                children=[
                    Text(value="Crédito Mes Anterior", size="sm", color="tertiary"),
                    Text(value=f"-{fmt(previous_month_credit)}", size="sm", color="tertiary"),
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
) -> str:
    """
    Generate human-readable fallback text for the tax calculation widget.

    Args:
        iva_collected: IVA débito fiscal (IVA cobrado)
        iva_paid: IVA crédito fiscal (IVA pagado)
        previous_month_credit: Crédito del mes anterior from F29
        monthly_tax: Final tax amount to pay
        period: Period string (e.g., "Oct 2025")

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
        f"IVA Neto: {fmt(iva_neto)}",
    ]

    if previous_month_credit is not None:
        lines.append(f"Crédito Mes Anterior: -{fmt(previous_month_credit)}")

    lines.append("")
    lines.append(f"Impuesto a Pagar: {fmt(monthly_tax)}")

    if previous_month_credit and iva_neto < previous_month_credit:
        remaining_credit = previous_month_credit - iva_neto
        lines.append("")
        lines.append(f"Remanente a favor: {fmt(remaining_credit)} para el próximo mes")

    return "\n".join(lines)


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


def create_person_confirmation_widget(
    action: str,  # "create" or "update"
    first_name: str,
    last_name: str,
    rut: str,
    position_title: str | None = None,
    hire_date: str | None = None,
    base_salary: float | None = None,
    contract_type: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    afp_provider: str | None = None,
    health_provider: str | None = None,
) -> WidgetRoot | None:
    """
    Create a widget displaying person information for confirmation before creating/updating.

    Args:
        action: "create" for new employee, "update" for existing
        first_name: Employee first name
        last_name: Employee last name
        rut: Employee RUT
        position_title: Job title (optional)
        hire_date: Hire date in ISO format (optional)
        base_salary: Monthly salary (optional)
        contract_type: Contract type (optional)
        email: Email address (optional)
        phone: Phone number (optional)
        afp_provider: AFP provider name (optional)
        health_provider: Health insurance provider (optional)

    Returns:
        Card widget with person confirmation details, or None if widgets not available
    """
    if not WIDGETS_AVAILABLE:
        return None

    # Format currency
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    # Format date
    def fmt_date(date_str: str) -> str:
        from datetime import datetime
        try:
            date_obj = datetime.fromisoformat(date_str)
            return date_obj.strftime("%d %b %Y")
        except:
            return date_str

    # Contract type mapping
    contract_types = {
        "indefinido": "Indefinido",
        "plazo_fijo": "Plazo Fijo",
        "honorarios": "Honorarios",
        "por_obra": "Por Obra",
        "part_time": "Part Time",
    }

    rows = []

    # Header
    icon = "➕" if action == "create" else "✏️"
    title = f"{icon} Confirmar Nuevo Colaborador" if action == "create" else f"{icon} Confirmar Actualización"

    rows.append(
        Box(
            padding=4,
            background="surface-tertiary",
            children=[
                Text(
                    value=title,
                    size="lg",
                    weight="semibold",
                )
            ],
        )
    )

    # Content
    content_rows = []

    # Personal Information Section
    content_rows.append(
        Text(value="👤 Información Personal", size="sm", weight="semibold", color="secondary")
    )

    personal_info = []
    personal_info.append(
        Row(
            justify="between",
            children=[
                Text(value="Nombre Completo", size="sm"),
                Text(value=f"{first_name} {last_name}", size="sm", weight="medium"),
            ],
        )
    )
    personal_info.append(
        Row(
            justify="between",
            children=[
                Text(value="RUT", size="sm"),
                Text(value=rut, size="sm", weight="medium"),
            ],
        )
    )
    if email:
        personal_info.append(
            Row(
                justify="between",
                children=[
                    Text(value="Email", size="sm"),
                    Text(value=email, size="sm", color="tertiary"),
                ],
            )
        )
    if phone:
        personal_info.append(
            Row(
                justify="between",
                children=[
                    Text(value="Teléfono", size="sm"),
                    Text(value=phone, size="sm", color="tertiary"),
                ],
            )
        )

    content_rows.append(
        Box(
            padding={"top": 2, "bottom": 3},
            gap=1,
            children=personal_info,
        )
    )

    # Contract Information Section (if available)
    if position_title or hire_date or contract_type:
        content_rows.append(
            Text(value="📄 Información Contractual", size="sm", weight="semibold", color="secondary")
        )

        contract_info = []
        if position_title:
            contract_info.append(
                Row(
                    justify="between",
                    children=[
                        Text(value="Cargo", size="sm"),
                        Text(value=position_title, size="sm", weight="medium"),
                    ],
                )
            )
        if contract_type:
            contract_info.append(
                Row(
                    justify="between",
                    children=[
                        Text(value="Tipo de Contrato", size="sm"),
                        Text(value=contract_types.get(contract_type, contract_type), size="sm", color="tertiary"),
                    ],
                )
            )
        if hire_date:
            contract_info.append(
                Row(
                    justify="between",
                    children=[
                        Text(value="Fecha de Ingreso", size="sm"),
                        Text(value=fmt_date(hire_date), size="sm", color="tertiary"),
                    ],
                )
            )

        content_rows.append(
            Box(
                padding={"top": 2, "bottom": 3},
                gap=1,
                children=contract_info,
            )
        )

    # Salary Section (if available)
    if base_salary:
        content_rows.append(
            Text(value="💰 Remuneración", size="sm", weight="semibold", color="secondary")
        )

        content_rows.append(
            Box(
                padding={"top": 2, "bottom": 3},
                children=[
                    Row(
                        justify="between",
                        children=[
                            Text(value="Sueldo Base Mensual", size="sm"),
                            Text(value=fmt(base_salary), size="md", weight="bold"),
                        ],
                    )
                ],
            )
        )

    # Impositions Section (if available)
    if afp_provider or health_provider:
        content_rows.append(
            Text(value="🏥 Imposiciones", size="sm", weight="semibold", color="secondary")
        )

        impositions_info = []
        if afp_provider:
            impositions_info.append(
                Row(
                    justify="between",
                    children=[
                        Text(value="AFP", size="sm"),
                        Text(value=afp_provider, size="sm", color="tertiary"),
                    ],
                )
            )
        if health_provider:
            impositions_info.append(
                Row(
                    justify="between",
                    children=[
                        Text(value="Salud", size="sm"),
                        Text(value=health_provider, size="sm", color="tertiary"),
                    ],
                )
            )

        content_rows.append(
            Box(
                padding={"top": 2, "bottom": 3},
                gap=1,
                children=impositions_info,
            )
        )

    # Wrap content
    rows.append(
        Box(
            padding=4,
            gap=2,
            children=content_rows,
        )
    )

    # Divider before buttons
    rows.append(Divider(flush=True))

    # Action buttons
    rows.append(
        Box(
            padding=4,
            gap=2,
            children=[
                Button(
                    label="✅ Confirmar",
                    onClickAction=ActionConfig(
                        type="confirm",
                        payload={},
                        loadingBehavior="self",  # Bloquea solo este botón mientras procesa
                    ),
                    style="primary",
                    block=True,
                ),
                Button(
                    label="❌ Rechazar",
                    onClickAction=ActionConfig(
                        type="cancel",
                        payload={},
                        loadingBehavior="self",  # Bloquea solo este botón mientras procesa
                    ),
                    style="secondary",
                    block=True,
                ),
            ],
        )
    )

    return Card(
        key="person_confirmation",
        padding=0,
        children=rows,
    )


def person_confirmation_widget_copy_text(
    action: str,
    first_name: str,
    last_name: str,
    rut: str,
    position_title: str | None = None,
    hire_date: str | None = None,
    base_salary: float | None = None,
    contract_type: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    afp_provider: str | None = None,
    health_provider: str | None = None,
) -> str:
    """
    Generate human-readable fallback text for the person confirmation widget.

    Args:
        Same as create_person_confirmation_widget

    Returns:
        Formatted text representation
    """
    def fmt(amount: float) -> str:
        return f"${amount:,.0f}"

    contract_types = {
        "indefinido": "Indefinido",
        "plazo_fijo": "Plazo Fijo",
        "honorarios": "Honorarios",
        "por_obra": "Por Obra",
        "part_time": "Part Time",
    }

    title = "Confirmar Nuevo Colaborador" if action == "create" else "Confirmar Actualización"
    lines = [title, "=" * len(title), ""]

    lines.append("Información Personal:")
    lines.append(f"  Nombre: {first_name} {last_name}")
    lines.append(f"  RUT: {rut}")
    if email:
        lines.append(f"  Email: {email}")
    if phone:
        lines.append(f"  Teléfono: {phone}")

    if position_title or hire_date or contract_type:
        lines.append("")
        lines.append("Información Contractual:")
        if position_title:
            lines.append(f"  Cargo: {position_title}")
        if contract_type:
            lines.append(f"  Tipo de Contrato: {contract_types.get(contract_type, contract_type)}")
        if hire_date:
            lines.append(f"  Fecha de Ingreso: {hire_date}")

    if base_salary:
        lines.append("")
        lines.append("Remuneración:")
        lines.append(f"  Sueldo Base Mensual: {fmt(base_salary)}")

    if afp_provider or health_provider:
        lines.append("")
        lines.append("Imposiciones:")
        if afp_provider:
            lines.append(f"  AFP: {afp_provider}")
        if health_provider:
            lines.append(f"  Salud: {health_provider}")

    lines.append("")
    lines.append("✅ Para confirmar, responde: 'Confirmar' o 'Sí'")
    lines.append("❌ Para cancelar, responde: 'Cancelar' o 'No'")

    return "\n".join(lines)
