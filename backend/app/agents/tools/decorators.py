"""
Tool Decorators - Subscription validation decorators for agent tools.

This module provides decorators to validate subscription access before
executing tool functions. If access is denied, a structured error response
is returned that the agent can process and communicate to the user.

Usage:
    @function_tool(strict_mode=False)
    @require_subscription_tool("get_f29_data")
    async def get_f29_data(ctx: RunContextWrapper[FizkoContext], ...):
        # Tool implementation
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable

from agents import RunContextWrapper

from app.agents.core import FizkoContext
from app.agents.core.subscription_responses import create_tool_block_response

logger = logging.getLogger(__name__)


def require_subscription_tool(tool_name: str) -> Callable:
    """
    Decorator to validate subscription access before executing a tool.

    This decorator checks if the company has access to the specified tool
    based on their subscription plan. If access is denied, it returns a
    structured error response that the agent can process.

    The decorator:
    1. Extracts company_id from context
    2. Checks tool access via SubscriptionGuard
    3. If blocked: Returns structured error response
    4. If allowed: Executes tool normally

    Args:
        tool_name: Name of the tool to check (e.g., "get_f29_data")

    Returns:
        Decorator function

    Example:
        ```python
        @function_tool(strict_mode=False)
        @require_subscription_tool("get_f29_data")
        async def get_f29_data(
            ctx: RunContextWrapper[FizkoContext],
            periodo: str
        ) -> dict[str, Any]:
            # This only runs if subscription check passes
            ...
        ```

    Response when blocked:
        ```python
        {
            "error": "subscription_required",
            "blocked": True,
            "blocked_type": "tool",
            "tool_name": "get_f29_data",
            "display_name": "Datos de Formulario 29",
            "plan_required": "pro",
            "user_message": "🔒 Datos de Formulario 29 requiere Plan Pro...",
            "benefits": ["...", "..."],
            "upgrade_url": "/configuracion/suscripcion",
            "alternative_message": "Puedo ayudarte con información general..."
        }
        ```

    The agent receiving this response can:
    - Inform the user about the limitation
    - Mention the benefits of upgrading
    - Offer alternative functionality if available
    - Guide user to upgrade page
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            ctx: RunContextWrapper[FizkoContext], *args: Any, **kwargs: Any
        ) -> dict[str, Any]:
            # Extract company_id from context
            company_id = ctx.context.request_context.get("company_id")

            if not company_id:
                logger.warning(
                    f"⚠️  Tool '{tool_name}' called without company_id in context"
                )
                return {
                    "error": "context_error",
                    "message": "company_id no disponible en el contexto",
                }

            # Verify tool access
            from app.config.database import AsyncSessionLocal
            from app.agents.core.subscription_guard import SubscriptionGuard

            async with AsyncSessionLocal() as db:
                guard = SubscriptionGuard(db)
                can_use, error_msg = await guard.can_use_tool(company_id, tool_name)

                if not can_use:
                    # Return structured block response
                    block_response = create_tool_block_response(tool_name)
                    logger.info(
                        f"🔒 Tool blocked: {tool_name} | Company: {company_id} | "
                        f"Plan required: {block_response['plan_required']}"
                    )
                    return block_response

            # Access granted - execute tool normally
            logger.debug(f"✅ Tool executing: {tool_name} | Company: {company_id}")
            return await func(ctx, *args, **kwargs)

        return wrapper

    return decorator


def require_subscription_feature(feature_key: str) -> Callable:
    """
    Decorator to validate generic feature access (not agent/tool specific).

    Similar to require_subscription_tool but for generic features that
    don't fit the agent/tool pattern.

    Args:
        feature_key: Feature key to check (e.g., "has_whatsapp", "has_api_access")

    Returns:
        Decorator function

    Example:
        ```python
        @function_tool(strict_mode=False)
        @require_subscription_feature("has_whatsapp")
        async def send_whatsapp_message(...):
            # Only runs if feature is enabled
            ...
        ```

    Response when blocked:
        ```python
        {
            "error": "feature_not_available",
            "message": "Esta funcionalidad requiere una suscripción activa.",
            "feature": "has_whatsapp",
            "upgrade_url": "/configuracion/suscripcion"
        }
        ```
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            ctx: RunContextWrapper[FizkoContext], *args: Any, **kwargs: Any
        ) -> dict[str, Any]:
            # Extract company_id from context
            company_id = ctx.context.request_context.get("company_id")

            if not company_id:
                logger.warning(
                    f"⚠️  Feature '{feature_key}' called without company_id in context"
                )
                return {
                    "error": "context_error",
                    "message": "company_id no disponible en el contexto",
                }

            # Verify feature access
            from app.config.database import AsyncSessionLocal
            from app.services.subscriptions import SubscriptionService

            async with AsyncSessionLocal() as db:
                service = SubscriptionService(db)
                has_access = await service.check_feature_access(company_id, feature_key)

                if not has_access:
                    logger.info(
                        f"🔒 Feature blocked: {feature_key} | Company: {company_id}"
                    )
                    return {
                        "error": "feature_not_available",
                        "message": f"Esta funcionalidad requiere una suscripción activa con acceso a '{feature_key}'.",
                        "feature": feature_key,
                        "upgrade_url": "/configuracion/suscripcion",
                    }

            # Access granted - execute tool normally
            logger.debug(f"✅ Feature access granted: {feature_key} | Company: {company_id}")
            return await func(ctx, *args, **kwargs)

        return wrapper

    return decorator


# Convenience decorators for common premium features
require_pro_plan = lambda func: require_subscription_feature("plan_level.pro")(func)
require_enterprise_plan = lambda func: require_subscription_feature(
    "plan_level.enterprise"
)(func)
