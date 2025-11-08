"""Subscription Upgrade Widget - Displays plan comparison and upgrade options."""

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


def create_subscription_upgrade_widget(
    blocked_item: str,  # "payroll", "advanced_tax", etc.
    display_name: str,  # "Nómina", "Impuestos Avanzados", etc.
    plan_required: str,  # "pro", "enterprise"
    benefits: list[str],  # List of benefits for the required plan
    current_plan: str | None = None,  # "free", "starter", "pro"
) -> WidgetRoot | None:
    """
    Create a widget displaying subscription upgrade information.

    Shows the feature that's blocked, the required plan, benefits, and an upgrade button.

    Args:
        blocked_item: Internal name of the blocked feature
        display_name: User-facing name of the blocked feature
        plan_required: The plan level required (e.g., "pro", "enterprise")
        benefits: List of benefits included in the required plan
        current_plan: User's current plan (optional, for display purposes)

    Returns:
        Card widget with subscription upgrade details, or None if widgets not available
    """
    if not WIDGETS_AVAILABLE:
        return None

    # Plan name formatting
    plan_names = {
        "free": "Gratuito",
        "starter": "Starter",
        "pro": "Pro",
        "enterprise": "Enterprise",
    }

    plan_display = plan_names.get(plan_required.lower(), plan_required.capitalize())
    current_plan_display = plan_names.get(current_plan.lower(), current_plan) if current_plan else None

    # Build benefit rows
    benefit_rows = []
    for benefit in benefits:
        benefit_rows.append(
            Row(
                children=[
                    Text("✓", color="green", weight="bold"),
                    Text(benefit, size="small"),
                ],
                gap="small",
            )
        )

    # Header section
    header_section = Box(
        children=[
            Text(f"🔒 {display_name}", size="large", weight="bold"),
            Text(
                f"Esta funcionalidad está disponible en el Plan {plan_display}",
                size="medium",
                color="secondary",
            ),
        ],
        gap="small",
    )

    # Current plan section (if available)
    current_plan_section = None
    if current_plan_display:
        current_plan_section = Box(
            children=[
                Text(f"Plan actual: {current_plan_display}", size="small", color="secondary"),
            ],
            gap="small",
        )

    # Benefits section
    benefits_section = Box(
        children=[
            Divider(),
            Text(f"Con el Plan {plan_display} podrás:", size="medium", weight="bold"),
            *benefit_rows,
        ],
        gap="medium",
    )

    # Build children list
    card_children = [header_section]

    if current_plan_section:
        card_children.append(current_plan_section)

    card_children.append(benefits_section)
    card_children.append(Divider())

    # Action buttons
    buttons_row = Row(
        children=[
            Button(
                "Ver Planes",
                action=ActionConfig(
                    type="link",
                    href="/configuracion/suscripcion",
                ),
                variant="primary",
            ),
            Button(
                "Más Tarde",
                action=ActionConfig(
                    type="respond",
                    text="No, gracias. Prefiero continuar con mi plan actual.",
                ),
                variant="secondary",
            ),
        ],
        gap="medium",
    )

    card_children.append(buttons_row)

    # Create the card
    card = Card(
        children=card_children,
        padding="large",
        border_color="blue",
    )

    return WidgetRoot(root=card)


def subscription_upgrade_widget_copy_text(
    blocked_item: str,
    display_name: str,
    plan_required: str,
    benefits: list[str],
    current_plan: str | None = None,
) -> str:
    """
    Generate copy text for the subscription upgrade widget.

    This is used as fallback when widgets are not available (e.g., WhatsApp).

    Args:
        blocked_item: Internal name of the blocked feature
        display_name: User-facing name of the blocked feature
        plan_required: The plan level required
        benefits: List of benefits
        current_plan: User's current plan (optional)

    Returns:
        Formatted text representation of the upgrade prompt
    """
    plan_names = {
        "free": "Gratuito",
        "starter": "Starter",
        "pro": "Pro",
        "enterprise": "Enterprise",
    }

    plan_display = plan_names.get(plan_required.lower(), plan_required.capitalize())
    current_plan_display = plan_names.get(current_plan.lower(), current_plan) if current_plan else None

    lines = [
        f"🔒 {display_name}",
        "",
        f"Esta funcionalidad está disponible en el Plan {plan_display}.",
    ]

    if current_plan_display:
        lines.append(f"Tu plan actual: {current_plan_display}")
        lines.append("")

    lines.append(f"Con el Plan {plan_display} podrás:")
    for benefit in benefits:
        lines.append(f"  ✓ {benefit}")

    lines.append("")
    lines.append("¿Te gustaría conocer más sobre los planes disponibles?")
    lines.append("Puedes verlos en: Configuración > Suscripción")

    return "\n".join(lines)
