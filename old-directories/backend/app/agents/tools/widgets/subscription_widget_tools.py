"""Subscription Widget Tools - Interactive UI for subscription upgrades."""

from __future__ import annotations

import logging
from typing import Any

from agents import RunContextWrapper, function_tool

from ...core import FizkoContext
from .widgets import (
    create_subscription_upgrade_widget,
    subscription_upgrade_widget_copy_text,
)

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
async def show_subscription_upgrade(
    ctx: RunContextWrapper[FizkoContext],
    blocked_item: str,  # "payroll", "advanced_tax", etc.
    display_name: str,  # "Nómina", "Impuestos Avanzados", etc.
    plan_required: str,  # "pro", "enterprise"
    benefits: list[str],  # List of benefits for the required plan
) -> dict[str, Any]:
    """
    Show a subscription upgrade widget when a feature is blocked.

    This tool displays an interactive card with:
    - The blocked feature name
    - The required plan
    - List of benefits included in that plan
    - "Ver Planes" button that redirects to /configuracion/suscripcion
    - "Más Tarde" button to dismiss

    Args:
        blocked_item: Internal name of the blocked feature (e.g., "payroll")
        display_name: User-facing name of the blocked feature (e.g., "Nómina")
        plan_required: The plan level required (e.g., "pro", "enterprise")
        benefits: List of benefits included in the required plan

    Returns:
        Dict with widget data and copy text for channels without widget support

    Example:
        await show_subscription_upgrade(
            ctx=ctx,
            blocked_item="payroll",
            display_name="Nómina",
            plan_required="pro",
            benefits=[
                "Gestión completa de empleados",
                "Liquidaciones de sueldo automatizadas",
                "Cálculo de imposiciones (AFP, Salud, AFC)",
                "Contratos y finiquitos digitales",
                "Reportes de nómina personalizados"
            ]
        )
    """
    logger.info(f"🔒 Showing subscription upgrade widget: {blocked_item} → {plan_required}")

    # Get current plan from context if available
    current_plan = None
    if ctx.state and hasattr(ctx.state, "request_context"):
        request_context = ctx.state.request_context
        # Try to get current plan from company info
        if "current_plan" in request_context:
            current_plan = request_context["current_plan"]

    # Create widget
    widget = create_subscription_upgrade_widget(
        blocked_item=blocked_item,
        display_name=display_name,
        plan_required=plan_required,
        benefits=benefits,
        current_plan=current_plan,
    )

    # Generate copy text for fallback (WhatsApp, etc.)
    copy_text = subscription_upgrade_widget_copy_text(
        blocked_item=blocked_item,
        display_name=display_name,
        plan_required=plan_required,
        benefits=benefits,
        current_plan=current_plan,
    )

    result = {
        "success": True,
        "widget": widget,
        "copy_text": copy_text,
        "blocked_item": blocked_item,
        "plan_required": plan_required,
    }

    logger.info(f"✅ Subscription upgrade widget created for {blocked_item}")
    return result
