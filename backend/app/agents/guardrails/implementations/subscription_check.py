"""Subscription Limit Guardrail - Enforces usage limits based on subscription tier."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent, RunContextWrapper, input_guardrail
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.guardrails.core import GuardrailFunctionOutput

logger = logging.getLogger(__name__)


@input_guardrail
async def subscription_limit_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input_data: str | list[dict[str, Any]],
) -> GuardrailFunctionOutput:
    """
    Checks if the user has exceeded their subscription limits.

    Limits can include:
    - Number of AI queries per month
    - Number of documents processed
    - Number of F29 forms analyzed
    - Access to premium features

    This is a lightweight check that runs before expensive AI operations.
    """
    # Extract company_id from context
    company_id = None
    if hasattr(ctx, "context") and hasattr(ctx.context, "request_context"):
        company_id = ctx.context.request_context.get("company_id")

    if not company_id:
        # No company_id means no limits (anonymous user or testing)
        return GuardrailFunctionOutput(
            output_info={"status": "no_company_id"},
            tripwire_triggered=False,
        )

    # TODO: Implement actual subscription limit checks
    # For now, this is a placeholder that always passes

    # Example implementation:
    """
    try:
        from app.agents.core.subscription_guard import SubscriptionGuard

        # Get DB session (if available in context)
        db: AsyncSession = getattr(ctx.context, "db", None)
        if db:
            guard = SubscriptionGuard(db)

            # Check if company has exceeded monthly query limit
            has_exceeded = await guard.check_query_limit(company_id)
            if has_exceeded:
                logger.warning(f"🚨 Subscription limit exceeded for company: {company_id}")
                return GuardrailFunctionOutput(
                    output_info={
                        "reason": "Monthly query limit exceeded",
                        "company_id": str(company_id),
                    },
                    tripwire_triggered=True,
                )
    except Exception as e:
        logger.error(f"❌ Subscription check failed: {e}")
        # Don't block on guardrail failure
        pass
    """

    return GuardrailFunctionOutput(
        output_info={"status": "ok"},
        tripwire_triggered=False,
    )
