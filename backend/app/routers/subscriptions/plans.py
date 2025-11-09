"""Subscription plans router - List available plans."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.dependencies import SubscriptionServiceDep

router = APIRouter(prefix="/api/subscriptions/plans", tags=["subscriptions"])


@router.get("")
async def list_plans(
    response: Response,
    service: SubscriptionServiceDep
):
    """
    List all public subscription plans.

    Returns all active, public plans ordered by display order.
    No authentication required - plans are public information.

    Returns:
        List of plans with pricing and features
    """
    # Disable HTTP caching - always fetch fresh data
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    plans = await service.list_available_plans(include_private=False)

    # Plans are already dicts with calculated CLP prices from UF
    return {"plans": plans}


@router.get("/{plan_code}")
async def get_plan_details(
    plan_code: str,
    service: SubscriptionServiceDep
):
    """
    Get details of a specific plan by code.

    Args:
        plan_code: Plan code (e.g., "free", "basic", "pro")

    Returns:
        Plan details with all features
    """
    plan = await service.get_plan_by_code(plan_code)

    if not plan or not plan.is_public:
        return {"error": "Plan not found"}, 404

    return {
        "code": plan.code,
        "name": plan.name,
        "tagname": plan.tagname,
        "tagline": plan.tagline,
        "description": plan.description,
        "price_monthly": float(plan.price_monthly),
        "price_yearly": float(plan.price_yearly),
        "currency": plan.currency,
        "trial_days": plan.trial_days,
        "features": plan.features,
    }
