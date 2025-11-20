"""Subscription models for billing and plan management."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company


class SubscriptionPlan(Base):
    """
    Subscription plan definitions (Free, Basic, Pro, Enterprise).

    Plans define pricing and feature limits. Companies subscribe to plans
    via the Subscription model.
    """

    __tablename__ = "subscription_plans"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Plan identification
    code: Mapped[str] = mapped_column(Text, unique=True)  # e.g., "free", "basic", "pro"
    name: Mapped[str] = mapped_column(Text)  # e.g., "Plan Básico"
    tagname: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # e.g., "Conecta"
    tagline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # e.g., "Controla tu situación tributaria"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing
    price_monthly: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default=text("0"))
    price_yearly: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default=text("0"))
    currency: Mapped[str] = mapped_column(Text, server_default=text("'CLP'::text"))

    # Trial configuration
    trial_days: Mapped[int] = mapped_column(Integer, server_default=text("0"))  # 0 = no trial

    # Feature limits (stored as JSON for flexibility)
    features: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb"),
    )
    # Example features structure:
    # {
    #   "max_monthly_transactions": 100,  # null = unlimited
    #   "max_users": 1,
    #   "has_whatsapp": false,
    #   "has_ai_assistant": true,
    #   "has_sii_sync": true,
    #   "has_advanced_reports": false,
    #   "has_api_access": false,
    #   "support_level": "email"  # "email", "priority", "dedicated"
    # }

    # Display order and visibility
    display_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    is_public: Mapped[bool] = mapped_column(
        server_default=text("true"),
    )  # If false, plan is only available via admin assignment

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="plan"
    )


class Subscription(Base):
    """
    Company subscription to a plan.

    One-to-one with Company. Tracks billing cycle, payment status,
    and subscription lifecycle.
    """

    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign keys
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        unique=True
    )
    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscription_plans.id")
    )

    # Status
    status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'trialing'::text")
    )

    # Billing cycle
    interval: Mapped[str] = mapped_column(
        Text,
        server_default=text("'monthly'::text")
    )
    current_period_start: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    current_period_end: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))

    # Trial
    trial_start: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    trial_end: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(server_default=text("false"))
    canceled_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Payment (integration with payment provider)
    payment_provider: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # "stripe", "mercadopago", "flow", etc.
    external_subscription_id: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # ID from payment provider
    payment_method_id: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Additional metadata (renamed to avoid conflict with SQLAlchemy's metadata)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in DB
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint(
            "status = ANY (ARRAY['trialing'::text, 'active'::text, 'past_due'::text, "
            "'canceled'::text, 'incomplete'::text])",
            name="subscriptions_status_check",
        ),
        CheckConstraint(
            "interval = ANY (ARRAY['monthly'::text, 'yearly'::text])",
            name="subscriptions_interval_check",
        ),
    )

    # Relationships
    company: Mapped["Company"] = relationship(
        "Company", back_populates="subscription"
    )
    plan: Mapped["SubscriptionPlan"] = relationship(
        "SubscriptionPlan", back_populates="subscriptions"
    )
    usage_records: Mapped[list["SubscriptionUsage"]] = relationship(
        "SubscriptionUsage",
        back_populates="subscription",
        cascade="all, delete-orphan"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="subscription",
        cascade="all, delete-orphan"
    )


class SubscriptionUsage(Base):
    """
    Track usage metrics per subscription period.

    Resets at the start of each billing cycle. Used to enforce
    plan limits (e.g., max transactions, max users).
    """

    __tablename__ = "subscription_usage"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key
    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE")
    )

    # Period tracking
    period_start: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    period_end: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))

    # Usage counters
    monthly_transactions_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    active_users_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    api_calls_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    whatsapp_messages_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))

    # Additional usage metrics (flexible)
    usage_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship(
        "Subscription", back_populates="usage_records"
    )


class Invoice(Base):
    """
    Invoice/payment records for subscriptions.

    Tracks all billing attempts and payment history.
    """

    __tablename__ = "invoices"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key
    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE")
    )

    # Invoice details
    invoice_number: Mapped[str] = mapped_column(Text, unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(Text, server_default=text("'CLP'::text"))

    # Status
    status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'draft'::text")
    )  # draft, open, paid, void, uncollectible

    # Dates
    invoice_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Payment provider integration
    external_invoice_id: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    payment_intent_id: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Additional data (renamed to avoid conflict with SQLAlchemy's metadata)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in DB
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint(
            "status = ANY (ARRAY['draft'::text, 'open'::text, 'paid'::text, "
            "'void'::text, 'uncollectible'::text])",
            name="invoices_status_check",
        ),
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship(
        "Subscription", back_populates="invoices"
    )
