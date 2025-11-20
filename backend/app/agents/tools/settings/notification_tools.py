"""Notification preference management tools for settings agent - Stub for Backend V2."""

from __future__ import annotations

from agents import RunContextWrapper, function_tool
from typing import Optional, Any

from app.agents.core import FizkoContext


@function_tool(strict_mode=False)
async def list_notifications(ctx: RunContextWrapper[FizkoContext]) -> dict[str, Any]:
    """List all available notifications for the user's company (stub).

    Backend-v2 doesn't have notification system implemented yet.
    """
    return {
        "success": False,
        "error": "La gestión de notificaciones no está disponible en esta versión.",
        "available_notifications": [],
    }


@function_tool(strict_mode=False)
async def edit_notification(
    ctx: RunContextWrapper[FizkoContext],
    action: str,
    template_id: Optional[str] = None,
    template_name: Optional[str] = None,
) -> dict[str, Any]:
    """Enable, disable, mute, or unmute a notification for the user (stub).

    Backend-v2 doesn't have notification system implemented yet.
    """
    return {
        "success": False,
        "error": "La edición de notificaciones no está disponible en esta versión.",
    }
