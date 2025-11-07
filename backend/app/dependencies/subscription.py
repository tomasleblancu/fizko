"""Subscription and feature access dependencies."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from .company import get_user_company_id


async def get_subscription_service(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get subscription service with request-scoped cache.

    This ensures multiple subscription checks in the same request
    reuse the same service instance (with in-memory cache).

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        SubscriptionService: Service instance cached in request state

    Example:
        ```python
        @router.post("/endpoint")
        async def my_endpoint(
            service: SubscriptionServiceDep
        ):
            has_feature = await service.check_feature_access(
                company_id, "has_whatsapp"
            )
        ```
    """
    from ..services.subscriptions import SubscriptionService

    # Cache service in request state (avoids recreating service per check)
    if not hasattr(request.state, "subscription_service"):
        request.state.subscription_service = SubscriptionService(db)

    return request.state.subscription_service


# =============================================================================
# Feature Access Dependencies (reusable)
# =============================================================================


def require_feature(feature_key: str):
    """
    Factory function to create feature-checking dependencies.

    Creates a dependency that checks if the company's subscription
    includes a specific feature. Raises 403 if feature is not available.

    Args:
        feature_key: Feature key to check (e.g., "has_whatsapp", "has_ai_assistant")

    Returns:
        Dependency function that checks feature access

    Example:
        ```python
        @router.post("/whatsapp/send")
        async def send_message(
            company_id: UUID = Depends(get_user_company_id),
            _: None = Depends(require_feature("has_whatsapp"))
        ):
            # Feature check passed, proceed with endpoint logic
            ...
        ```

    Custom feature check:
        ```python
        require_custom_feature = require_feature("my_custom_feature")

        @router.get("/custom")
        async def my_endpoint(_: None = Depends(require_custom_feature)):
            ...
        ```
    """
    async def _check_feature(
        company_id: UUID = Depends(get_user_company_id),
        service = Depends(get_subscription_service)
    ) -> None:
        has_access = await service.check_feature_access(company_id, feature_key)

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "feature_not_available",
                    "message": f"Your subscription plan does not include '{feature_key}'.",
                    "feature": feature_key,
                    "upgrade_required": True
                }
            )

    return _check_feature


def check_usage_limit(limit_key: str):
    """
    Factory function to create usage-limit-checking dependencies.

    Creates a dependency that checks if the company is within
    their subscription's usage limits. Raises 429 if limit exceeded.

    Args:
        limit_key: Limit key to check (e.g., "max_monthly_transactions")

    Returns:
        Dependency function that checks usage limit

    Example:
        ```python
        @router.post("/documents")
        async def create_document(
            company_id: UUID = Depends(get_user_company_id),
            _: None = Depends(check_usage_limit("max_monthly_transactions"))
        ):
            # Limit check passed
            ...
        ```

    Custom limit check:
        ```python
        check_custom_limit = check_usage_limit("max_custom_items")

        @router.post("/custom")
        async def my_endpoint(_: None = Depends(check_custom_limit)):
            ...
        ```
    """
    async def _check_limit(
        company_id: UUID = Depends(get_user_company_id),
        service = Depends(get_subscription_service)
    ) -> None:
        within_limit, limit_value, current_value = await service.check_usage_limit(
            company_id, limit_key
        )

        if not within_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": f"Monthly limit exceeded for {limit_key}.",
                    "limit": limit_value,
                    "current": current_value,
                    "upgrade_required": True
                }
            )

    return _check_limit


# =============================================================================
# Pre-configured Feature Checks (convenience)
# =============================================================================

# Common feature checks - ready to use
require_whatsapp = require_feature("has_whatsapp")
require_ai_assistant = require_feature("has_ai_assistant")
require_advanced_reports = require_feature("has_advanced_reports")
require_api_access = require_feature("has_api_access")


# =============================================================================
# Pre-configured Limit Checks (convenience)
# =============================================================================

# Common limit checks - ready to use
check_transaction_limit = check_usage_limit("max_monthly_transactions")
check_user_limit = check_usage_limit("max_users")
check_api_call_limit = check_usage_limit("max_api_calls")
check_whatsapp_limit = check_usage_limit("max_whatsapp_messages")


# =============================================================================
# Helper: Get subscription info for endpoint response
# =============================================================================


async def get_subscription_info(
    company_id: UUID = Depends(get_user_company_id),
    service = Depends(get_subscription_service)
) -> dict:
    """
    Get subscription information for including in responses.

    Useful for endpoints that want to return subscription status
    alongside their main response.

    Args:
        company_id: Company ID from active session
        service: Subscription service

    Returns:
        Dictionary with subscription status and plan info

    Example:
        ```python
        @router.get("/status")
        async def get_status(
            sub_info: dict = Depends(get_subscription_info)
        ):
            return {
                "app_status": "healthy",
                "subscription": sub_info
            }
        ```
    """
    subscription = await service.get_company_subscription(company_id)

    if not subscription:
        return {
            "status": "none",
            "plan": None,
            "features": {}
        }

    return {
        "status": subscription.status,
        "plan": {
            "code": subscription.plan.code,
            "name": subscription.plan.name
        },
        "features": subscription.plan.features,
        "current_period_end": subscription.current_period_end.isoformat()
    }


# =============================================================================
# Global Subscription Check (any active subscription required)
# =============================================================================


async def get_subscription_or_none(
    company_id: UUID = Depends(get_user_company_id),
    service = Depends(get_subscription_service)
):
    """
    Get subscription for company without blocking request.

    Returns subscription if exists, None if not. Does NOT raise exceptions.
    Useful for endpoints that want to check subscription but not block access.

    Args:
        company_id: Company ID from active session
        service: Subscription service

    Returns:
        Subscription instance if exists, None otherwise

    Example:
        ```python
        @router.get("/endpoint")
        async def my_endpoint(
            subscription: Optional[Subscription] = Depends(get_subscription_or_none)
        ):
            if subscription:
                # User has subscription, provide full features
                ...
            else:
                # User doesn't have subscription, provide limited features
                ...
        ```
    """
    from ..db.models import Subscription

    try:
        subscription = await service.get_company_subscription(company_id)
        # Only return if subscription is active
        if subscription and subscription.status in ['trialing', 'active']:
            return subscription
        return None
    except Exception:
        # If any error occurs, return None (don't block request)
        return None


async def require_active_subscription(
    company_id: UUID = Depends(get_user_company_id),
    service = Depends(get_subscription_service)
):
    """
    Require company to have an active subscription.

    This is a global check that blocks access if the company doesn't have
    any active subscription. It doesn't check features or limits - just
    verifies that a subscription exists and is active.

    Blocks access if:
    - No subscription exists
    - Subscription status is 'canceled', 'past_due', or 'incomplete'

    Allows access if:
    - Subscription status is 'trialing' or 'active'
    - Any plan (basic, pro, etc.)

    Args:
        company_id: Company ID from active session
        service: Subscription service

    Returns:
        Subscription instance if active

    Raises:
        402 Payment Required if no active subscription

    Example:
        ```python
        @router.get("/endpoint")
        async def my_endpoint(
            subscription: Subscription = Depends(require_active_subscription)
        ):
            # User has active subscription, proceed
            ...
        ```

        Or as router dependency:
        ```python
        router = APIRouter(
            dependencies=[
                Depends(require_auth),
                Depends(require_active_subscription)
            ]
        )
        ```
    """
    from ..db.models import Subscription

    subscription = await service.get_company_subscription(company_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "subscription_required",
                "message": "Se requiere una suscripción activa para acceder a esta funcionalidad.",
                "action": "create_subscription"
            }
        )

    # Check if subscription is active
    if subscription.status not in ['trialing', 'active']:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "subscription_inactive",
                "message": f"Tu suscripción está {subscription.status}. Reactiva tu suscripción para continuar.",
                "status": subscription.status,
                "action": "reactivate_subscription"
            }
        )

    return subscription


# =============================================================================
# Type Aliases for Convenience
# =============================================================================

SubscriptionServiceDep = Annotated[object, Depends(get_subscription_service)]
ActiveSubscriptionDep = Annotated[object, Depends(require_active_subscription)]


__all__ = [
    # Service
    "get_subscription_service",
    "SubscriptionServiceDep",
    # Global subscription check
    "get_subscription_or_none",
    "require_active_subscription",
    "ActiveSubscriptionDep",
    # Factories
    "require_feature",
    "check_usage_limit",
    # Pre-configured feature checks
    "require_whatsapp",
    "require_ai_assistant",
    "require_advanced_reports",
    "require_api_access",
    # Pre-configured limit checks
    "check_transaction_limit",
    "check_user_limit",
    "check_api_call_limit",
    "check_whatsapp_limit",
    # Helpers
    "get_subscription_info",
]
