"""
Tool Decorators - Subscription validation decorators for agent tools (Stub for Backend V2).

Backend-v2 doesn't have subscription system, so these decorators are no-ops.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable

from agents import RunContextWrapper

from app.agents.core import FizkoContext

logger = logging.getLogger(__name__)


def require_subscription_tool(tool_name: str) -> Callable:
    """
    Decorator to validate subscription access before executing a tool (stub).

    In backend-v2, all tools are available (no subscription system).
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            ctx: RunContextWrapper[FizkoContext], *args: Any, **kwargs: Any
        ) -> dict[str, Any]:
            # No subscription validation in backend-v2 - just execute the tool
            logger.debug(f"✅ Tool executing (no subscription check): {tool_name}")
            return await func(ctx, *args, **kwargs)

        return wrapper

    return decorator


def require_subscription_feature(feature_key: str) -> Callable:
    """
    Decorator to validate generic feature access (stub).

    In backend-v2, all features are available (no subscription system).
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            ctx: RunContextWrapper[FizkoContext], *args: Any, **kwargs: Any
        ) -> dict[str, Any]:
            # No feature validation in backend-v2 - just execute the function
            logger.debug(f"✅ Feature access granted (no subscription check): {feature_key}")
            return await func(ctx, *args, **kwargs)

        return wrapper

    return decorator


# Convenience decorators for common premium features (all no-ops in backend-v2)
require_pro_plan = lambda func: func
require_enterprise_plan = lambda func: func
