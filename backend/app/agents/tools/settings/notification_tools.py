"""Notification preference management tools for settings agent."""

from __future__ import annotations

from agents import RunContextWrapper, function_tool
from typing import Optional, Any
from uuid import UUID

from ...core import FizkoContext
from ....config.database import AsyncSessionLocal


@function_tool(strict_mode=False)
async def list_notifications(ctx: RunContextWrapper[FizkoContext]) -> dict[str, Any]:
    """List all available notifications for the user's company.

    Returns information about:
    - Global notification preferences (enabled/disabled)
    - All notification templates the company is subscribed to
    - Which notifications are currently active or muted for the user

    This tool helps users see what notifications are available and their current status.

    Returns:
        dict: Contains:
            - notifications_enabled: bool - Whether notifications are globally enabled
            - available_notifications: list - All notifications the company is subscribed to
            - muted_templates: list - Template IDs that are currently muted
    """
    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    try:
        async with AsyncSessionLocal() as session:
            # Lazy import to avoid circular dependency
            from ....services.notifications import get_notification_service

            # Get notification service
            notification_service = get_notification_service()

            # Get user's notification preferences
            user_prefs = await notification_service.get_user_preferences(
                db=session,
                user_id=UUID(user_id),
                company_id=UUID(company_id),
            )

            # Get company subscriptions
            subscriptions = await notification_service.get_company_subscriptions(
                db=session,
                company_id=UUID(company_id),
            )

            # Build response
            notifications_enabled = user_prefs.get("notifications_enabled", True)
            muted_templates = user_prefs.get("muted_templates", [])

            available_notifications = []
            for sub in subscriptions:
                # Load template relationship if not loaded
                if not hasattr(sub, 'notification_template') or sub.notification_template is None:
                    await session.refresh(sub, ['notification_template'])

                template = sub.notification_template
                is_muted = str(template.id) in muted_templates

                available_notifications.append({
                    "template_id": str(template.id),
                    "name": template.name,
                    "description": template.description,
                    "category": template.category,
                    "is_enabled": sub.is_enabled,
                    "is_muted": is_muted,
                    "status": "muted" if is_muted else ("active" if sub.is_enabled else "disabled"),
                })

            return {
                "success": True,
                "notifications_enabled": notifications_enabled,
                "available_notifications": available_notifications,
                "muted_templates": muted_templates,
                "total_count": len(available_notifications),
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error al obtener notificaciones: {str(e)}",
        }


@function_tool(strict_mode=False)
async def edit_notification(
    ctx: RunContextWrapper[FizkoContext],
    action: str,
    template_id: Optional[str] = None,
    template_name: Optional[str] = None,
) -> dict[str, Any]:
    """Enable, disable, mute, or unmute a notification for the user.

    This tool allows users to control their notification preferences. Users can:
    - Enable/disable all notifications globally
    - Mute/unmute specific notification templates by ID or name

    Args:
        action: The action to perform. Valid values:
            - "enable_all": Enable all notifications globally
            - "disable_all": Disable all notifications globally
            - "mute": Mute a specific notification template
            - "unmute": Unmute a specific notification template
        template_id: UUID of the notification template (required for mute/unmute actions)
        template_name: Name of the notification template (alternative to template_id)

    Returns:
        dict: Contains:
            - success: bool - Whether the operation succeeded
            - message: str - Human-readable result message
            - error: str - Error message if failed

    Examples:
        # Disable all notifications
        edit_notification(context, action="disable_all")

        # Mute a specific notification by name
        edit_notification(context, action="mute", template_name="Recordatorio F29")

        # Unmute a specific notification by ID
        edit_notification(context, action="unmute", template_id="uuid-here")
    """
    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    try:
        # Validate action
        valid_actions = ["enable_all", "disable_all", "mute", "unmute"]
        if action not in valid_actions:
            return {
                "success": False,
                "error": f"Acción inválida. Usa una de: {', '.join(valid_actions)}",
            }

        async with AsyncSessionLocal() as session:
            # Lazy import to avoid circular dependency
            from ....services.notifications import get_notification_service

            # Get notification service
            notification_service = get_notification_service()

            # Get current user preferences
            user_prefs = await notification_service.get_user_preferences(
                db=session,
                user_id=UUID(user_id),
                company_id=UUID(company_id),
            )

            # Handle global enable/disable
            if action == "enable_all":
                await notification_service.update_user_preferences(
                    db=session,
                    user_id=UUID(user_id),
                    company_id=UUID(company_id),
                    notifications_enabled=True,
                )
                return {
                    "success": True,
                    "message": "Todas las notificaciones han sido activadas.",
                }

            elif action == "disable_all":
                await notification_service.update_user_preferences(
                    db=session,
                    user_id=UUID(user_id),
                    company_id=UUID(company_id),
                    notifications_enabled=False,
                )
                return {
                    "success": True,
                    "message": "Todas las notificaciones han sido desactivadas.",
                }

            # Handle mute/unmute - need template_id or template_name
            if not template_id and not template_name:
                return {
                    "success": False,
                    "error": "Debes proporcionar template_id o template_name para mute/unmute.",
                }

            # Find template by ID or name
            if template_id:
                template = await notification_service.get_template(
                    db=session,
                    template_id=UUID(template_id),
                )
            else:
                # Search by name - get all templates and filter
                all_templates = await notification_service.list_templates(
                    db=session,
                    is_active=True,
                )
                template = None
                for t in all_templates:
                    if template_name.lower() in t.name.lower():
                        template = t
                        break

            if not template:
                return {
                    "success": False,
                    "error": f"No se encontró la notificación con {'ID' if template_id else 'nombre'} '{template_id or template_name}'.",
                }

            # Get current muted templates
            muted_templates = user_prefs.get("muted_templates", [])
            template_id_str = str(template.id)

            if action == "mute":
                if template_id_str not in muted_templates:
                    new_muted = muted_templates + [template_id_str]
                    await notification_service.update_user_preferences(
                        db=session,
                        user_id=UUID(user_id),
                        company_id=UUID(company_id),
                        muted_templates=new_muted,
                    )
                    return {
                        "success": True,
                        "message": f"La notificación '{template.name}' ha sido silenciada.",
                    }
                else:
                    return {
                        "success": True,
                        "message": f"La notificación '{template.name}' ya estaba silenciada.",
                    }

            elif action == "unmute":
                if template_id_str in muted_templates:
                    new_muted = [t for t in muted_templates if t != template_id_str]
                    await notification_service.update_user_preferences(
                        db=session,
                        user_id=UUID(user_id),
                        company_id=UUID(company_id),
                        muted_templates=new_muted,
                    )
                    return {
                        "success": True,
                        "message": f"La notificación '{template.name}' ha sido reactivada.",
                    }
                else:
                    return {
                        "success": True,
                        "message": f"La notificación '{template.name}' ya estaba activa.",
                    }

            return {
                "success": False,
                "error": "Acción no implementada.",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error al editar notificación: {str(e)}",
        }
