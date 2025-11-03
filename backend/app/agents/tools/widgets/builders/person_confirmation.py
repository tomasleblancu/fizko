"""Person Confirmation Widget - Displays employee confirmation details."""

from __future__ import annotations

from typing import Any

try:
    from chatkit.actions import ActionConfig
    from chatkit.widgets import Box, Button, Card, Divider, Row, Text, WidgetRoot
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False
    # Fallback types for type hints
    Card = Any  # type: ignore
    WidgetRoot = Any  # type: ignore
    Box = Any  # type: ignore
    Row = Any  # type: ignore
    Text = Any  # type: ignore
    Button = Any  # type: ignore
    Divider = Any  # type: ignore
    ActionConfig = Any  # type: ignore


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
