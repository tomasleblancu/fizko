"""Subscription service for managing subscriptions and enforcing limits."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Company, CompanyBrain, Subscription, SubscriptionPlan, SubscriptionUsage


class SubscriptionLimitExceeded(Exception):
    """Raised when a usage limit is exceeded."""

    def __init__(self, limit_name: str, limit_value: int, current_value: int):
        self.limit_name = limit_name
        self.limit_value = limit_value
        self.current_value = current_value
        super().__init__(
            f"Subscription limit exceeded: {limit_name}. "
            f"Limit: {limit_value}, Current: {current_value}"
        )


class SubscriptionService:
    """
    Service for managing subscriptions and enforcing limits.

    Handles:
    - Subscription CRUD operations
    - Feature access checks
    - Usage limit enforcement
    - Plan upgrades/downgrades
    - Subscription cancellation
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        # Request-scoped cache to avoid redundant queries
        self._cache: dict[UUID, Subscription] = {}

    async def get_company_subscription(
        self,
        company_id: UUID,
        use_cache: bool = True
    ) -> Optional[Subscription]:
        """
        Get active subscription for a company.

        Args:
            company_id: Company ID
            use_cache: Use in-memory cache (default True for performance)

        Returns:
            Subscription instance or None
        """
        # Check cache first
        if use_cache and company_id in self._cache:
            return self._cache[company_id]

        result = await self.db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.usage_records)
            )
            .where(Subscription.company_id == company_id)
        )
        subscription = result.scalar_one_or_none()

        if use_cache and subscription:
            self._cache[company_id] = subscription

        return subscription

    async def create_subscription(
        self,
        company_id: UUID,
        plan_code: str = "free",
        interval: str = "monthly"
    ) -> Subscription:
        """
        Create a new subscription for a company.

        Args:
            company_id: Company ID
            plan_code: Plan code (e.g., "free", "basic", "pro")
            interval: Billing interval ("monthly" or "yearly")

        Returns:
            Created subscription

        Raises:
            ValueError: If plan not found or subscription already exists
        """
        # Check if subscription already exists
        existing = await self.get_company_subscription(company_id, use_cache=False)
        if existing:
            raise ValueError(f"Subscription already exists for company {company_id}")

        # Get plan
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.code == plan_code)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError(f"Plan not found: {plan_code}")

        # Calculate trial period
        now = datetime.utcnow()
        trial_end = now + timedelta(days=plan.trial_days) if plan.trial_days > 0 else None

        # Determine status
        status = "trialing" if trial_end else "active"

        # Calculate billing period
        if interval == "monthly":
            period_end = now + timedelta(days=30)
        else:  # yearly
            period_end = now + timedelta(days=365)

        # Create subscription
        subscription = Subscription(
            company_id=company_id,
            plan_id=plan.id,
            status=status,
            interval=interval,
            current_period_start=now,
            current_period_end=period_end,
            trial_start=now if trial_end else None,
            trial_end=trial_end
        )

        self.db.add(subscription)
        await self.db.flush()

        # Create initial usage record
        await self._create_usage_record(subscription)

        await self.db.commit()
        await self.db.refresh(subscription)

        # Update cache
        self._cache[company_id] = subscription

        return subscription

    async def _create_usage_record(self, subscription: Subscription) -> SubscriptionUsage:
        """Create a new usage record for the current period."""
        usage = SubscriptionUsage(
            subscription_id=subscription.id,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end
        )
        self.db.add(usage)
        await self.db.flush()
        return usage

    async def check_feature_access(
        self,
        company_id: UUID,
        feature_key: str
    ) -> bool:
        """
        Check if a company has access to a specific feature.

        Args:
            company_id: Company ID
            feature_key: Feature key (e.g., "has_whatsapp", "has_ai_assistant")

        Returns:
            True if company has access, False otherwise
        """
        subscription = await self.get_company_subscription(company_id)
        if not subscription:
            return False

        # Check if subscription is active
        if subscription.status not in ['trialing', 'active']:
            return False

        # Check feature in plan
        return subscription.plan.features.get(feature_key, False)

    async def check_usage_limit(
        self,
        company_id: UUID,
        limit_key: str
    ) -> tuple[bool, Optional[int], Optional[int]]:
        """
        Check if a company is within usage limits.

        Args:
            company_id: Company ID
            limit_key: Limit key (e.g., "max_monthly_transactions")

        Returns:
            Tuple of (within_limit, limit_value, current_value)
            - within_limit: True if within limit or unlimited
            - limit_value: The limit value (None if unlimited)
            - current_value: Current usage count
        """
        subscription = await self.get_company_subscription(company_id)
        if not subscription:
            return False, None, None

        # Get limit from plan
        limit_value = subscription.plan.features.get(limit_key)
        if limit_value is None:  # No limit = unlimited
            return True, None, 0

        # Get current usage
        current_usage = await self._get_current_usage(subscription)
        if not current_usage:
            return True, limit_value, 0

        # Map limit key to usage field
        usage_field_map = {
            "max_monthly_transactions": "monthly_transactions_count",
            "max_users": "active_users_count",
            "max_api_calls": "api_calls_count",
            "max_whatsapp_messages": "whatsapp_messages_count"
        }

        usage_field = usage_field_map.get(limit_key)
        if not usage_field:
            return True, limit_value, 0

        current_value = getattr(current_usage, usage_field, 0)
        within_limit = current_value < limit_value

        return within_limit, limit_value, current_value

    async def increment_usage(
        self,
        company_id: UUID,
        usage_type: str,
        increment: int = 1
    ) -> None:
        """
        Increment usage counter for a company.

        Args:
            company_id: Company ID
            usage_type: Type of usage (e.g., "transactions", "api_calls")
            increment: Amount to increment

        Raises:
            SubscriptionLimitExceeded: If limit is exceeded
            ValueError: If subscription not found or unknown usage type
        """
        subscription = await self.get_company_subscription(company_id)
        if not subscription:
            raise ValueError(f"No subscription found for company {company_id}")

        # Get or create current usage record
        current_usage = await self._get_current_usage(subscription)
        if not current_usage:
            current_usage = await self._create_usage_record(subscription)

        # Map usage type to field and limit
        usage_field_map = {
            "transactions": ("monthly_transactions_count", "max_monthly_transactions"),
            "api_calls": ("api_calls_count", "max_api_calls"),
            "whatsapp_messages": ("whatsapp_messages_count", "max_whatsapp_messages")
        }

        if usage_type not in usage_field_map:
            raise ValueError(f"Unknown usage type: {usage_type}")

        field_name, limit_key = usage_field_map[usage_type]

        # Check limit before incrementing
        limit_value = subscription.plan.features.get(limit_key)
        if limit_value is not None:  # None = unlimited
            current_value = getattr(current_usage, field_name)
            if current_value + increment > limit_value:
                raise SubscriptionLimitExceeded(
                    limit_name=limit_key,
                    limit_value=limit_value,
                    current_value=current_value
                )

        # Increment counter
        setattr(current_usage, field_name, getattr(current_usage, field_name) + increment)
        await self.db.commit()

    async def _get_current_usage(self, subscription: Subscription) -> Optional[SubscriptionUsage]:
        """Get the current usage record for a subscription."""
        result = await self.db.execute(
            select(SubscriptionUsage)
            .where(SubscriptionUsage.subscription_id == subscription.id)
            .where(SubscriptionUsage.period_start == subscription.current_period_start)
        )
        return result.scalar_one_or_none()

    async def get_plan_by_code(self, plan_code: str) -> Optional[SubscriptionPlan]:
        """Get a subscription plan by its code."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.code == plan_code)
        )
        return result.scalar_one_or_none()

    async def list_available_plans(self, include_private: bool = False) -> list[dict]:
        """
        List all available subscription plans with UF-calculated prices.

        Args:
            include_private: Include private plans (default False)

        Returns:
            List of subscription plans with real-time CLP prices calculated from UF
        """
        # Use the view that calculates prices from UF dynamically
        query_text = """
            SELECT
                id,
                code,
                name,
                tagname,
                tagline,
                description,
                price_monthly_uf,
                price_yearly_uf,
                price_monthly,
                price_yearly,
                current_uf_value,
                currency,
                trial_days,
                features,
                display_order,
                is_active,
                is_public,
                created_at,
                updated_at
            FROM subscription_plans_with_clp
            WHERE is_active = true
        """

        if not include_private:
            query_text += " AND is_public = true"

        query_text += " ORDER BY display_order"

        result = await self.db.execute(text(query_text))
        rows = result.fetchall()

        # Convert to dict list for easier serialization
        plans = []
        for row in rows:
            plans.append({
                "id": str(row.id),
                "code": row.code,
                "name": row.name,
                "tagname": row.tagname,
                "tagline": row.tagline,
                "description": row.description,
                "price_monthly_uf": float(row.price_monthly_uf) if row.price_monthly_uf else None,
                "price_yearly_uf": float(row.price_yearly_uf) if row.price_yearly_uf else None,
                "price_monthly": float(row.price_monthly) if row.price_monthly else 0,
                "price_yearly": float(row.price_yearly) if row.price_yearly else 0,
                "current_uf_value": float(row.current_uf_value) if row.current_uf_value else None,
                "currency": row.currency,
                "trial_days": row.trial_days,
                "features": row.features,
                "display_order": row.display_order
            })

        return plans

    async def upgrade_plan(
        self,
        company_id: UUID,
        new_plan_code: str
    ) -> Subscription:
        """
        Upgrade/downgrade a subscription plan.

        Args:
            company_id: Company ID
            new_plan_code: New plan code

        Returns:
            Updated subscription

        Raises:
            ValueError: If subscription or plan not found
        """
        subscription = await self.get_company_subscription(company_id, use_cache=False)
        if not subscription:
            raise ValueError(f"No subscription found for company {company_id}")

        # Get new plan
        new_plan = await self.get_plan_by_code(new_plan_code)
        if not new_plan:
            raise ValueError(f"Plan not found: {new_plan_code}")

        # Update subscription
        subscription.plan_id = new_plan.id
        subscription.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(subscription)

        # Clear cache
        self._cache.pop(company_id, None)

        return subscription

    async def cancel_subscription(
        self,
        company_id: UUID,
        immediate: bool = False
    ) -> Subscription:
        """
        Cancel a subscription.

        Args:
            company_id: Company ID
            immediate: Cancel immediately (default False, cancels at period end)

        Returns:
            Updated subscription

        Raises:
            ValueError: If subscription not found
        """
        subscription = await self.get_company_subscription(company_id, use_cache=False)
        if not subscription:
            raise ValueError(f"No subscription found for company {company_id}")

        now = datetime.utcnow()

        if immediate:
            subscription.status = "canceled"
            subscription.canceled_at = now
            subscription.current_period_end = now
        else:
            subscription.cancel_at_period_end = True
            subscription.canceled_at = now

        await self.db.commit()
        await self.db.refresh(subscription)

        # Clear cache
        self._cache.pop(company_id, None)

        return subscription

    async def reactivate_subscription(self, company_id: UUID) -> Subscription:
        """
        Reactivate a canceled subscription.

        Args:
            company_id: Company ID

        Returns:
            Reactivated subscription

        Raises:
            ValueError: If subscription not found or not canceled
        """
        subscription = await self.get_company_subscription(company_id, use_cache=False)
        if not subscription:
            raise ValueError(f"No subscription found for company {company_id}")

        if subscription.status != "canceled":
            raise ValueError("Subscription is not canceled")

        # Reactivate
        subscription.status = "active"
        subscription.cancel_at_period_end = False
        subscription.canceled_at = None

        # Extend period if needed
        now = datetime.utcnow()
        if subscription.current_period_end < now:
            if subscription.interval == "monthly":
                subscription.current_period_end = now + timedelta(days=30)
            else:  # yearly
                subscription.current_period_end = now + timedelta(days=365)

        await self.db.commit()
        await self.db.refresh(subscription)

        # Clear cache
        self._cache.pop(company_id, None)

        return subscription

    async def subscription_has_changed(
        self,
        company_id: UUID,
        current_plan_code: str,
        current_status: str
    ) -> bool:
        """
        Check if subscription has changed compared to stored memory.

        Returns True if:
        - No memory exists (first time)
        - Plan code changed
        - Status changed

        Args:
            company_id: Company UUID
            current_plan_code: Current subscription plan code (e.g., "free", "pro")
            current_status: Current subscription status (e.g., "active", "trialing")

        Returns:
            True if subscription changed or no memory exists, False otherwise
        """
        # Query existing subscription memory
        result = await self.db.execute(
            select(CompanyBrain).where(
                CompanyBrain.company_id == company_id,
                CompanyBrain.slug == "company_subscription_plan"
            )
        )
        memory = result.scalar_one_or_none()

        # No memory exists - first time
        if not memory:
            return True

        # Parse stored memory content to extract plan code and status
        content = memory.content.lower()

        # Check if plan code or status changed
        # Memory format: "Plan de suscripción actual: {name} ({code}). Estado: {status}."
        plan_code_changed = f"({current_plan_code.lower()})" not in content

        # Map status to Spanish for comparison
        status_map = {
            "trialing": "en período de prueba",
            "active": "activo",
            "past_due": "con pago pendiente",
            "canceled": "cancelado",
            "incomplete": "incompleto",
        }
        status_spanish = status_map.get(current_status.lower(), current_status.lower())
        status_changed = status_spanish not in content

        # Special case: free plan check
        if current_plan_code == "free":
            # Check if "sin suscripción activa" is in content
            is_free_in_memory = "sin suscripción activa" in content
            if not is_free_in_memory:
                return True  # Changed to free plan
            # If already free, no change
            return False

        return plan_code_changed or status_changed
