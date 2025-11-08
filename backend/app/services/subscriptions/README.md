# Subscription Memory Sync System

## Overview

This system automatically syncs subscription data to the company memory system (Mem0) whenever subscription information is accessed or modified. This allows AI agents to be aware of a company's current subscription plan and features, enabling them to:

1. Show appropriate upgrade prompts when users hit plan limits
2. Provide contextual information about available features
3. Understand trial status and expiration

## Architecture

```
API Endpoint
    ↓
Fetch Subscription
    ↓
save_subscription_memories() ← Sync point
    ↓
Celery Task (async)
    ↓
Mem0 + company_brain table
```

## Files

### [memories.py](./memories.py)

Service that builds and saves subscription memories:

- `_build_subscription_memories(subscription)` - Builds memory objects with slugs
- `save_subscription_memories(company_id, subscription)` - Dispatches Celery task

### Integration Points

The memory sync is triggered in [backend/app/routers/subscriptions/current.py](../../routers/subscriptions/current.py) at these endpoints:

1. `GET /api/subscriptions/current` - When frontend checks subscription (or returns free plan if none)
2. `POST /api/subscriptions` - When creating new subscription
3. `POST /api/subscriptions/upgrade` - When upgrading/downgrading
4. `POST /api/subscriptions/cancel` - When canceling subscription
5. `POST /api/subscriptions/reactivate` - When reactivating canceled subscription

## Memory Structure

The system creates up to 3 memory entries per company:

**Note:** When a company has no active subscription, the system returns and syncs a "free" plan by default instead of returning a 404 error. This ensures AI agents always have subscription context.

### 1. company_subscription_plan

**Slug:** `company_subscription_plan`
**Category:** `company_subscription`

Contains current plan name, code, and status.

**Example:**
```
Plan de suscripción actual: Plan Pro (pro). Estado: activo.
```

### 2. company_subscription_features

**Slug:** `company_subscription_features`
**Category:** `company_subscription`

Lists available features and limits based on plan.features.

**Example:**
```
Funcionalidades disponibles: integración con WhatsApp, asistente de IA, sincronización con SII, reportes avanzados. Límites: 1000 transacciones mensuales, 10 usuario(s).
```

### 3. company_subscription_trial (optional)

**Slug:** `company_subscription_trial`
**Category:** `company_subscription`

Present only when subscription status is "trialing" and trial_end is set.

**Example:**
```
La empresa está en período de prueba del plan Plan Básico. Quedan 13 días de prueba (termina el 21/11/2025).
```

## Status Mapping

Subscription statuses are mapped to Spanish for better agent understanding:

| Status      | Spanish Display         |
|-------------|------------------------|
| trialing    | en período de prueba   |
| active      | activo                 |
| past_due    | con pago pendiente     |
| canceled    | cancelado              |
| incomplete  | incompleto             |

## Feature Detection

The system automatically detects and includes features based on plan.features:

**Boolean Features:**
- `has_whatsapp` → "integración con WhatsApp"
- `has_ai_assistant` → "asistente de IA"
- `has_sii_sync` → "sincronización con SII"
- `has_advanced_reports` → "reportes avanzados"
- `has_api_access` → "acceso a API"

**Limit Features:**
- `max_monthly_transactions` → "X transacciones mensuales"
- `max_users` → "X usuario(s)"

## How AI Agents Use This

1. **Supervisor Agent** searches company memory when routing requests
2. Agent sees subscription plan and available features
3. If agent is blocked (via subscription guards), it detects this from memory
4. Supervisor can show upgrade widget with `show_subscription_upgrade()` tool

## Example Flow

```
User (free plan): "Muéstrame mis ventas de enero"
    ↓
Supervisor checks memory: "Plan: Gratuito (free)"
    ↓
Attempts to route to tax_documents agent
    ↓
Agent is blocked (requires basic plan)
    ↓
Returns blocking response with plan requirements
    ↓
Supervisor calls show_subscription_upgrade()
    ↓
User sees upgrade widget with benefits
```

## Celery Task

The actual memory save operation is handled by [backend/app/infrastructure/celery/tasks/memory/company.py](../../infrastructure/celery/tasks/memory/company.py):

- **Task name:** `memory.save_company_memories`
- **Max retries:** 3
- **Retry delay:** 60 seconds
- **Non-blocking:** Dispatched via `.delay()`

## Testing

Basic unit tests are provided in the file via mock objects:

```python
from app.services.subscriptions.memories import _build_subscription_memories

# Test with active subscription
subscription = MockSubscription(status="active", plan=MockPlan(...))
memories = _build_subscription_memories(subscription)
# Returns 2 memories: plan + features

# Test with trial subscription
subscription = MockSubscription(status="trialing", trial_end=future_date)
memories = _build_subscription_memories(subscription)
# Returns 3 memories: plan + features + trial
```

## Future Enhancements

Potential improvements:

1. **Usage tracking in memory** - Include current usage vs limits
2. **Expiration warnings** - Alert agents when subscription is expiring soon
3. **Feature-specific memories** - Separate memory for each major feature
4. **Historical tracking** - Track subscription changes over time
5. **Smart prompting** - Agents proactively suggest upgrades based on usage patterns
