"""Current subscription router - Manage user's active subscription."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import CompanyIdDep, require_auth, SubscriptionServiceDep

router = APIRouter(
    prefix="/api/subscriptions",
    tags=["subscriptions"],
    dependencies=[Depends(require_auth)]
)


class SubscriptionCreateRequest(BaseModel):
    """Request to create a new subscription."""
    plan_code: str
    interval: str = "monthly"  # monthly or yearly


class SubscriptionUpgradeRequest(BaseModel):
    """Request to upgrade/downgrade subscription."""
    new_plan_code: str


@router.get("/current")
async def get_current_subscription(
    company_id: CompanyIdDep,
    service: SubscriptionServiceDep
):
    """
    Get current subscription for the user's company.

    Returns:
        Current subscription with plan details and usage
    """
    subscription = await service.get_company_subscription(company_id)

    if not subscription:
        # Return null for no subscription (frontend expects null, not an object with subscription: None)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )

    # Check if subscription is in trial
    is_trial = (
        subscription.status == "trialing" and
        subscription.trial_end is not None
    )

    return {
        "status": subscription.status,
        "plan": {
            "code": subscription.plan.code,
            "name": subscription.plan.name,
            "tagname": subscription.plan.tagname
        },
        "features": subscription.plan.features,
        "current_period_end": subscription.current_period_end.isoformat(),
        "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None,
        "is_trial": is_trial
    }


@router.post("")
async def create_subscription(
    request: SubscriptionCreateRequest,
    company_id: CompanyIdDep,
    service: SubscriptionServiceDep
):
    """
    Create a new subscription for the company.

    Args:
        request: Subscription creation request with plan_code and interval

    Returns:
        Created subscription

    Raises:
        400: If subscription already exists
        404: If plan not found
    """
    try:
        subscription = await service.create_subscription(
            company_id=company_id,
            plan_code=request.plan_code,
            interval=request.interval
        )

        return {
            "id": str(subscription.id),
            "status": subscription.status,
            "message": f"Subscription to {subscription.plan.name} created successfully!",
            "trial_days": subscription.plan.trial_days if subscription.trial_end else 0
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/usage")
async def get_usage(
    company_id: CompanyIdDep,
    service: SubscriptionServiceDep
):
    """
    Get current usage statistics for the subscription.

    Returns:
        Usage statistics with limits
    """
    subscription = await service.get_company_subscription(company_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )

    usage = await service._get_current_usage(subscription)

    # Build response with limits
    features = subscription.plan.features

    return {
        "period_start": subscription.current_period_start.isoformat(),
        "period_end": subscription.current_period_end.isoformat(),
        "transactions": {
            "used": usage.monthly_transactions_count if usage else 0,
            "limit": features.get("max_monthly_transactions"),
            "unlimited": features.get("max_monthly_transactions") is None
        },
        "users": {
            "active": usage.active_users_count if usage else 0,
            "limit": features.get("max_users"),
            "unlimited": features.get("max_users") is None
        },
        "api_calls": {
            "used": usage.api_calls_count if usage else 0,
            "limit": features.get("max_api_calls"),
            "unlimited": features.get("max_api_calls") is None
        },
        "whatsapp_messages": {
            "used": usage.whatsapp_messages_count if usage else 0,
            "limit": features.get("max_whatsapp_messages"),
            "unlimited": features.get("max_whatsapp_messages") is None
        }
    }


@router.post("/upgrade")
async def upgrade_subscription(
    request: SubscriptionUpgradeRequest,
    company_id: CompanyIdDep,
    service: SubscriptionServiceDep
):
    """
    Upgrade or downgrade subscription plan.

    Args:
        request: Upgrade request with new_plan_code

    Returns:
        Updated subscription

    Raises:
        404: If subscription or plan not found
    """
    try:
        subscription = await service.upgrade_plan(
            company_id=company_id,
            new_plan_code=request.new_plan_code
        )

        return {
            "message": f"Subscription upgraded to {subscription.plan.name}",
            "plan": {
                "code": subscription.plan.code,
                "name": subscription.plan.name
            }
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/cancel")
async def cancel_subscription(
    company_id: CompanyIdDep,
    service: SubscriptionServiceDep,
    immediate: bool = False
):
    """
    Cancel subscription.

    Args:
        immediate: Cancel immediately (default False, cancels at period end)

    Returns:
        Canceled subscription status

    Raises:
        404: If subscription not found
    """
    try:
        subscription = await service.cancel_subscription(
            company_id=company_id,
            immediate=immediate
        )

        return {
            "message": "Subscription canceled" + (" immediately" if immediate else " at period end"),
            "canceled_at": subscription.canceled_at.isoformat(),
            "access_until": subscription.current_period_end.isoformat()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/reactivate")
async def reactivate_subscription(
    company_id: CompanyIdDep,
    service: SubscriptionServiceDep
):
    """
    Reactivate a canceled subscription.

    Returns:
        Reactivated subscription

    Raises:
        404: If subscription not found
        400: If subscription is not canceled
    """
    try:
        subscription = await service.reactivate_subscription(company_id=company_id)

        return {
            "message": "Subscription reactivated successfully",
            "status": subscription.status,
            "period_end": subscription.current_period_end.isoformat()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
