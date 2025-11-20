"""
Webhook handlers for external services.

Currently handles:
- Mem0 memory events (memory.created, memory.updated, memory.deleted)
"""
import hashlib
import hmac
import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select

from app.config.database import AsyncSessionLocal
from app.db.models import UserBrain, CompanyBrain
from app.repositories import UserBrainRepository, CompanyBrainRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_mem0_signature(payload: str, signature: Optional[str], secret: str) -> bool:
    """
    Verify Mem0 webhook signature using HMAC-SHA256.

    Args:
        payload: Raw request body as string
        signature: X-Webhook-Signature header value
        secret: MEM0_WEBHOOK_SECRET from environment

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        return False

    # Compute HMAC-SHA256
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Compare signatures (constant-time comparison)
    return hmac.compare_digest(signature, expected_signature)


@router.post("/mem0")
async def handle_mem0_webhook(
    request: Request,
    x_webhook_secret: Optional[str] = Header(None, alias="x-webhook-secret"),
) -> Dict[str, Any]:
    """
    Handle Mem0 webhook events.

    This endpoint receives notifications when memories are processed by Mem0.
    When a memory moves from PENDING to COMPLETED, we update our Brain records
    with the actual memory_id.

    Expected events:
    - ADD: When a memory is successfully created
    - UPDATE: When a memory is updated
    - DELETE: When a memory is deleted

    Payload structure:
    {
        "event_details": {
            "id": "mem_12345",           # The actual memory ID
            "event": "ADD",              # Event type
            "user_id": "company_uuid",   # Entity ID
            "data": {
                "memory": "..."
            }
        }
    }
    """
    try:
        # Get raw payload
        body = await request.body()
        payload = body.decode("utf-8")

        # Validate webhook secret (Mem0 sends it directly in header)
        webhook_secret = os.getenv("MEM0_WEBHOOK_SECRET")

        if webhook_secret:
            if not x_webhook_secret:
                logger.warning("[Mem0 Webhook] ⚠️ Missing x-webhook-secret header")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing x-webhook-secret header",
                )

            if x_webhook_secret != webhook_secret:
                logger.error("[Mem0 Webhook] ❌ Invalid webhook secret")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook secret",
                )

            logger.info("[Mem0 Webhook] ✅ Secret verified")
        else:
            logger.warning(
                "[Mem0 Webhook] ⚠️ MEM0_WEBHOOK_SECRET not configured - "
                "webhook validation disabled"
            )

        # Parse payload
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            logger.error(f"[Mem0 Webhook] ❌ Invalid JSON payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload",
            )

        # Extract event data - Mem0 uses "event_details" wrapper
        event_details = data.get("event_details", {})
        event_type = event_details.get("event")  # "ADD", "UPDATE", "DELETE"
        event_id = event_details.get("id")  # The memory ID from Mem0
        user_id = event_details.get("user_id")  # Entity ID (company_xxx or user uuid)
        event_data = event_details.get("data", {})

        logger.info(f"[Mem0 Webhook] Processing event: {event_type}")
        logger.info(f"[Mem0 Webhook] Event ID: {event_id}")
        logger.info(f"[Mem0 Webhook] User ID: {user_id}")
        logger.info(f"[Mem0 Webhook] Event data: {event_data}")

        # Process based on event type - Mem0 uses: ADD, UPDATE, DELETE
        if event_type == "ADD":
            await handle_memory_added(event_id, user_id, event_data)
        elif event_type == "UPDATE":
            await handle_memory_updated_mem0(event_id, user_id, event_data)
        elif event_type == "DELETE":
            await handle_memory_deleted_mem0(event_id, user_id)
        else:
            logger.warning(f"[Mem0 Webhook] Unknown event type: {event_type}")

        return {
            "status": "success",
            "message": f"Webhook processed: {event_type}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Mem0 Webhook] ❌ Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook",
        )


async def handle_memory_added(memory_id: str, user_id: str, event_data: Dict[str, Any]) -> None:
    """
    Handle ADD event from Mem0.

    When a new memory is created in Mem0, this webhook is called with the final memory_id.

    Strategy:
    1. Check if this memory_id already exists in our database (idempotency)
    2. If not, this is a new memory being directly created by Mem0
    3. Log and return - no update needed since the memory was likely created with the final ID

    Args:
        memory_id: The memory ID from Mem0 (event_details.id)
        user_id: Entity ID (company_xxx or user uuid)
        event_data: Additional event data
    """
    logger.info(
        f"[Mem0 Webhook] 🧠 Memory added - "
        f"memory_id: {memory_id}, user_id: {user_id}"
    )

    if not memory_id or not user_id:
        logger.warning(f"[Mem0 Webhook] Skipping - missing memory_id or user_id")
        return

    # Determine if this is a company or user memory
    is_company = user_id.startswith("company_")

    async with AsyncSessionLocal() as db:
        try:
            if is_company:
                # Extract company_id from user_id
                company_id = user_id.replace("company_", "")
                repo = CompanyBrainRepository(db)

                # Check if this memory_id already exists (idempotency)
                existing = await repo.get_by_memory_id(memory_id)
                if existing:
                    logger.info(
                        f"[Mem0 Webhook] ✅ Memory already exists in database - "
                        f"memory_id: {memory_id}, slug: {existing.slug} (idempotent)"
                    )
                    return

                # Memory doesn't exist yet - this is a new memory created directly
                # with the final ID (no event_id intermediate state)
                logger.info(
                    f"[Mem0 Webhook] ℹ️ New memory created in Mem0 - "
                    f"memory_id: {memory_id}, company_id: {company_id}"
                )
            else:
                # User memory
                repo = UserBrainRepository(db)

                # Check if this memory_id already exists (idempotency)
                existing = await repo.get_by_memory_id(memory_id)
                if existing:
                    logger.info(
                        f"[Mem0 Webhook] ✅ Memory already exists in database - "
                        f"memory_id: {memory_id}, slug: {existing.slug} (idempotent)"
                    )
                    return

                # Memory doesn't exist yet - this is a new memory
                logger.info(
                    f"[Mem0 Webhook] ℹ️ New memory created in Mem0 - "
                    f"memory_id: {memory_id}, user_id: {user_id}"
                )

        except Exception as e:
            logger.error(
                f"[Mem0 Webhook] ❌ Error processing ADD event: {e}",
                exc_info=True
            )


async def handle_memory_updated_mem0(memory_id: str, user_id: str, event_data: Dict[str, Any]) -> None:
    """
    Handle UPDATE event from Mem0.

    Args:
        memory_id: The memory ID
        user_id: Entity ID
        event_data: Event data
    """
    logger.info(f"[Mem0 Webhook] 🔄 Memory updated - memory_id: {memory_id}")


async def handle_memory_deleted_mem0(memory_id: str, user_id: str) -> None:
    """
    Handle DELETE event from Mem0.

    Args:
        memory_id: The memory ID
        user_id: Entity ID
    """
    logger.info(
        f"[Mem0 Webhook] 🗑️ Memory deleted - "
        f"memory_id: {memory_id}, user_id: {user_id}"
    )

    # Optionally delete the corresponding Brain record
    # For now, we'll just log it
    # The cascade delete on company/user deletion will handle cleanup
