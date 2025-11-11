"""
Subscription Helper for Celery Tasks

Helper functions to check subscription status in background tasks.
These functions are designed to be used in Celery tasks to conditionally
execute operations based on company subscription status.

Usage in Celery tasks:
    from app.infrastructure.celery.subscription_helper import check_company_subscription

    async def _sync():
        async with get_background_db() as db:
            # Check if company has active subscription
            has_subscription = await check_company_subscription(db, company_id)
            if not has_subscription:
                logger.info(f"⏭️  Skipping company {company_id}: No active subscription")
                return None

            # Continue with sync logic...
"""
import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def check_company_subscription(
    db: AsyncSession,
    company_id: UUID | str,
) -> bool:
    """
    Check if a company has an active subscription (trialing or active).

    This is a lightweight check designed for background tasks that should
    only run for subscribed companies (like document syncing, F29 extraction, etc.)

    Args:
        db: Async database session
        company_id: Company ID as UUID or string

    Returns:
        True if company has active or trialing subscription, False otherwise

    Example:
        >>> async with get_background_db() as db:
        >>>     has_sub = await check_company_subscription(db, company_id)
        >>>     if not has_sub:
        >>>         logger.info("Skipping: no subscription")
        >>>         return
    """
    try:
        from app.db.models import Subscription

        # Convert to UUID if needed
        if isinstance(company_id, str):
            company_id = UUID(company_id)

        # Query for active subscription
        stmt = select(Subscription).where(
            Subscription.company_id == company_id,
            Subscription.status.in_(["trialing", "active"])
        )
        result = await db.execute(stmt)
        subscription = result.scalar_one_or_none()

        return subscription is not None

    except Exception as e:
        logger.error(
            f"❌ Error checking subscription for company {company_id}: {e}",
            exc_info=True
        )
        # In case of error, default to False (don't execute task)
        return False


async def get_subscribed_companies(
    db: AsyncSession,
    only_active: bool = True
) -> list[tuple[UUID, str]]:
    """
    Get all companies with active subscriptions.

    This is useful for batch operations that should only run on subscribed companies.

    Args:
        db: Async database session
        only_active: Deprecated parameter (kept for backwards compatibility, no effect)

    Returns:
        List of tuples (company_id, business_name) for subscribed companies

    Example:
        >>> async with get_background_db() as db:
        >>>     subscribed = await get_subscribed_companies(db)
        >>>     for company_id, name in subscribed:
        >>>         logger.info(f"Processing {name}")
    """
    try:
        from app.db.models import Company, Subscription

        # Build query - only check subscription status
        # Note: Company.is_active field no longer exists
        stmt = (
            select(Company.id, Company.business_name)
            .join(Subscription, Company.id == Subscription.company_id)
            .where(Subscription.status.in_(["trialing", "active"]))
        )

        result = await db.execute(stmt)
        companies = result.all()

        return [(row[0], row[1]) for row in companies]

    except Exception as e:
        logger.error(
            f"❌ Error getting subscribed companies: {e}",
            exc_info=True
        )
        return []
