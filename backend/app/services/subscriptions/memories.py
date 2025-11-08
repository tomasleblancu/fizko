"""
Subscription Memories Service

Manages the synchronization of subscription data into the company memory system (Mem0).
This allows AI agents to be aware of the company's current subscription plan and features.

The service follows the same pattern as onboarding and settings memories:
1. Build memory objects with slug, category, and content
2. Dispatch Celery task to save asynchronously
3. Task updates or creates memories in Mem0 and company_brain table
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.db.models import Subscription, SubscriptionPlan

logger = logging.getLogger(__name__)


def _build_subscription_memories(subscription: Subscription) -> list[dict]:
    """
    Build memory objects for a company's subscription data.

    Creates memories that describe:
    - Current subscription plan
    - Subscription status
    - Available features

    Args:
        subscription: Subscription model instance with loaded plan relationship

    Returns:
        List of memory dicts with slug, category, and content
    """
    memories = []

    # Get plan info
    plan = subscription.plan
    plan_code = plan.code if plan else "free"
    plan_name = plan.name if plan else "Gratuito"
    status = subscription.status

    # Map status to Spanish
    status_map = {
        "trialing": "en período de prueba",
        "active": "activo",
        "past_due": "con pago pendiente",
        "canceled": "cancelado",
        "incomplete": "incompleto",
    }
    status_display = status_map.get(status, status)

    # Memory 1: Subscription plan
    memories.append({
        "slug": "company_subscription_plan",
        "category": "company_subscription",
        "content": (
            f"Plan de suscripción actual: {plan_name} ({plan_code}). "
            f"Estado: {status_display}."
        )
    })

    # Memory 2: Subscription features (if plan has features)
    if plan and plan.features:
        features_list = []

        # Extract boolean features
        if plan.features.get("has_whatsapp"):
            features_list.append("integración con WhatsApp")
        if plan.features.get("has_ai_assistant"):
            features_list.append("asistente de IA")
        if plan.features.get("has_sii_sync"):
            features_list.append("sincronización con SII")
        if plan.features.get("has_advanced_reports"):
            features_list.append("reportes avanzados")
        if plan.features.get("has_api_access"):
            features_list.append("acceso a API")

        # Extract limits
        max_transactions = plan.features.get("max_monthly_transactions")
        max_users = plan.features.get("max_users")

        limits_text = []
        if max_transactions:
            limits_text.append(f"{max_transactions} transacciones mensuales")
        if max_users:
            limits_text.append(f"{max_users} usuario(s)")

        # Build features memory
        content_parts = []
        if features_list:
            content_parts.append(f"Funcionalidades disponibles: {', '.join(features_list)}.")
        if limits_text:
            content_parts.append(f"Límites: {', '.join(limits_text)}.")

        if content_parts:
            memories.append({
                "slug": "company_subscription_features",
                "category": "company_subscription",
                "content": " ".join(content_parts)
            })

    # Memory 3: Trial information (if in trial)
    is_trial = subscription.status == "trialing" and subscription.trial_end is not None
    if is_trial:
        from datetime import datetime, timezone

        trial_end = subscription.trial_end
        if trial_end.tzinfo is None:
            trial_end = trial_end.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        days_left = (trial_end - now).days

        memories.append({
            "slug": "company_subscription_trial",
            "category": "company_subscription",
            "content": (
                f"La empresa está en período de prueba del plan {plan_name}. "
                f"Quedan {days_left} días de prueba (termina el {trial_end.strftime('%d/%m/%Y')})."
            )
        })

    return memories


def _build_free_plan_memories(free_plan: Optional[SubscriptionPlan] = None) -> list[dict]:
    """
    Build memory objects for a company with no active subscription (free plan).

    Args:
        free_plan: Optional SubscriptionPlan model for "free" plan (if exists in DB)

    Returns:
        List of memory dicts with slug, category, and content
    """
    memories = []

    # Get plan info (use free_plan if provided, otherwise defaults)
    plan_code = free_plan.code if free_plan else "free"
    plan_name = free_plan.name if free_plan else "Gratuito"

    # Memory 1: Subscription plan (no active subscription)
    memories.append({
        "slug": "company_subscription_plan",
        "category": "company_subscription",
        "content": (
            f"Plan de suscripción actual: {plan_name} ({plan_code}). "
            f"Sin suscripción activa."
        )
    })

    # Memory 2: Free plan features (if free_plan has features)
    if free_plan and free_plan.features:
        features_list = []

        # Extract boolean features
        if free_plan.features.get("has_whatsapp"):
            features_list.append("integración con WhatsApp")
        if free_plan.features.get("has_ai_assistant"):
            features_list.append("asistente de IA")
        if free_plan.features.get("has_sii_sync"):
            features_list.append("sincronización con SII")

        # Extract limits
        max_transactions = free_plan.features.get("max_monthly_transactions")
        max_users = free_plan.features.get("max_users")

        limits_text = []
        if max_transactions:
            limits_text.append(f"{max_transactions} transacciones mensuales")
        if max_users:
            limits_text.append(f"{max_users} usuario(s)")

        # Build features memory
        content_parts = []
        if features_list:
            content_parts.append(f"Funcionalidades disponibles: {', '.join(features_list)}.")
        if limits_text:
            content_parts.append(f"Límites: {', '.join(limits_text)}.")

        if content_parts:
            memories.append({
                "slug": "company_subscription_features",
                "category": "company_subscription",
                "content": " ".join(content_parts)
            })
    else:
        # Generic free plan features
        memories.append({
            "slug": "company_subscription_features",
            "category": "company_subscription",
            "content": "Plan gratuito con funcionalidades limitadas."
        })

    return memories


def save_subscription_memories(
    company_id: str,
    subscription: Optional[Subscription] = None,
    free_plan: Optional[SubscriptionPlan] = None
) -> None:
    """
    Save subscription memories for a company (async via Celery).

    This function dispatches a Celery task to update the company's subscription
    data in the memory system. The task runs asynchronously to avoid blocking
    the API response.

    Handles two cases:
    1. Active subscription: Uses subscription data
    2. No subscription: Uses free plan (fallback to generic free plan)

    Args:
        company_id: Company UUID as string
        subscription: Optional Subscription model instance with loaded plan relationship
        free_plan: Optional SubscriptionPlan for free tier (used when subscription is None)

    Example:
        >>> # With active subscription
        >>> save_subscription_memories(str(company.id), subscription=subscription)
        >>>
        >>> # Without subscription (free plan)
        >>> save_subscription_memories(str(company.id), free_plan=free_plan)
    """
    # Build memories based on whether there's an active subscription
    if subscription:
        memories = _build_subscription_memories(subscription)
    else:
        memories = _build_free_plan_memories(free_plan)

    if not memories:
        logger.warning(f"No subscription memories generated for company {company_id}")
        return

    # Import here to avoid circular imports
    from app.infrastructure.celery.tasks.memory import save_company_memories_task

    # Dispatch Celery task (non-blocking)
    plan_type = "active subscription" if subscription else "free plan"
    logger.info(f"📝 Dispatching subscription memories save task for company {company_id} ({plan_type})")
    logger.info(f"   Memories to save: {len(memories)}")

    save_company_memories_task.delay(
        company_id=company_id,
        memories=memories
    )

    logger.info(f"✅ Subscription memories task dispatched for company {company_id}")
